from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Avg, Count, Min
from django.http import JsonResponse
from .models import University, UniversityRating, UniversityComparison, Region, UniversityType, News, Faculty, Program, UniversityRepresentative
from .forms import UniversitySearchForm, UniversityRatingForm, UniversityComparisonForm, NewsForm, UniversityEditForm, BecomeRepresentativeForm
from accounts.models import FavoriteUniversity


def home_view(request):
    """Главная страница"""
    # Топ университетов по рейтингу
    top_universities = University.objects.annotate(
        avg_rating=Avg('ratings__rating'),
        ratings_count=Count('ratings')
    ).filter(ratings_count__gte=1).order_by('-avg_rating')[:6]
    
    # Последние новости
    latest_news = News.objects.filter(is_published=True).order_by('-created_at')[:5]
    
    # Статистика
    total_universities = University.objects.count()
    total_regions = Region.objects.count()
    total_ratings = UniversityRating.objects.count()
    
    context = {
        'top_universities': top_universities,
        'latest_news': latest_news,
        'total_universities': total_universities,
        'total_regions': total_regions,
        'total_ratings': total_ratings,
    }
    return render(request, 'universities/home.html', context)


def university_list_view(request):
    """Список университетов с поиском и фильтрацией"""
    form = UniversitySearchForm(request.GET)
    universities = University.objects.all()
    
    if form.is_valid():
        name = form.cleaned_data.get('name')
        region = form.cleaned_data.get('region')
        city = form.cleaned_data.get('city')
        university_type = form.cleaned_data.get('university_type')
        is_public = form.cleaned_data.get('is_public')
        min_programs = form.cleaned_data.get('min_programs')
        max_tuition = form.cleaned_data.get('max_tuition')
        
        # Базовые фильтры
        if name:
            universities = universities.filter(name__icontains=name)
        if region:
            universities = universities.filter(region=region)
        if city:
            universities = universities.filter(city__icontains=city)
        if university_type:
            universities = universities.filter(university_type=university_type)
        if is_public is not None and is_public:
            universities = universities.filter(is_public=True)
    
    # Добавляем аннотации для всех нужных полей
    universities = universities.annotate(
        avg_rating=Avg('ratings__rating'),
        ratings_count=Count('ratings'),
        programs_count=Count('faculties__programs', distinct=True),
        min_tuition_fee=Min('faculties__programs__tuition_fee')
    )
    
    # Фильтрация по аннотированным полям
    if form.is_valid():
        min_rating = form.cleaned_data.get('min_rating')
        min_programs = form.cleaned_data.get('min_programs')
        max_tuition = form.cleaned_data.get('max_tuition')
        
        if min_rating:
            universities = universities.filter(avg_rating__gte=min_rating)
        if min_programs:
            universities = universities.filter(programs_count__gte=min_programs)
        if max_tuition:
            # Фильтруем по минимальной стоимости обучения среди программ
            universities = universities.filter(
                Q(min_tuition_fee__lte=max_tuition) | Q(min_tuition_fee__isnull=True)
            )
    
    # Сортировка: сначала по рейтингу, потом по количеству программ, затем по названию
    universities = universities.order_by('-avg_rating', '-programs_count', 'name')
    
    # Пагинация
    paginator = Paginator(universities, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Получаем уникальные города для автодополнения
    cities = University.objects.values_list('city', flat=True).distinct().order_by('city')
    
    context = {
        'form': form,
        'page_obj': page_obj,
        'universities': page_obj,
        'cities': cities,
    }
    return render(request, 'universities/university_list.html', context)


def university_detail_view(request, university_id):
    """Детальная страница университета"""
    university = get_object_or_404(University, id=university_id)
    
    # Проверяем, есть ли университет в избранном у пользователя
    is_favorite = False
    if request.user.is_authenticated:
        is_favorite = FavoriteUniversity.objects.filter(
            user=request.user,
            university=university
        ).exists()
    
    # Получаем рейтинги
    ratings = UniversityRating.objects.filter(university=university).order_by('-created_at')
    
    # Статистика рейтингов
    rating_stats = UniversityRating.objects.filter(university=university).aggregate(
        avg_rating=Avg('rating'),
        ratings_count=Count('rating')
    )
    
    # Факультеты и программы
    faculties = Faculty.objects.filter(university=university)
    programs = Program.objects.filter(faculty__university=university)
    
    # Новости университета
    news = News.objects.filter(university=university, is_published=True).order_by('-created_at')[:5]
    
    # Проверяем, является ли пользователь представителем
    is_representative = is_university_representative(request.user, university)
    
    context = {
        'university': university,
        'is_favorite': is_favorite,
        'ratings': ratings,
        'rating_stats': rating_stats,
        'faculties': faculties,
        'programs': programs,
        'news': news,
        'is_representative': is_representative,
    }
    return render(request, 'universities/university_detail.html', context)


@login_required
def rate_university_view(request, university_id):
    """Оценка университета"""
    university = get_object_or_404(University, id=university_id)
    
    # Проверяем, есть ли уже оценка от пользователя
    existing_rating = UniversityRating.objects.filter(
        university=university,
        user=request.user
    ).first()
    
    if request.method == 'POST':
        form = UniversityRatingForm(request.POST, instance=existing_rating)
        if form.is_valid():
            rating = form.save(commit=False)
            rating.university = university
            rating.user = request.user
            rating.save()
            messages.success(request, 'Спасибо за вашу оценку!')
            return redirect('universities:university_detail', university_id=university_id)
    else:
        form = UniversityRatingForm(instance=existing_rating)
    
    context = {
        'university': university,
        'form': form,
        'existing_rating': existing_rating,
    }
    return render(request, 'universities/rate_university.html', context)


def comparison_view(request):
    """Сравнение университетов"""
    # Получаем фильтры из GET запроса
    search_form = UniversitySearchForm(request.GET)
    universities = University.objects.all()
    
    # Применяем фильтры
    if search_form.is_valid():
        name = search_form.cleaned_data.get('name')
        region = search_form.cleaned_data.get('region')
        city = search_form.cleaned_data.get('city')
        university_type = search_form.cleaned_data.get('university_type')
        is_public = search_form.cleaned_data.get('is_public')
        
        if name:
            universities = universities.filter(name__icontains=name)
        if region:
            universities = universities.filter(region=region)
        if city:
            universities = universities.filter(city__icontains=city)
        if university_type:
            universities = universities.filter(university_type=university_type)
        if is_public is not None and is_public:
            universities = universities.filter(is_public=True)
    
    # Добавляем аннотации
    universities = universities.annotate(
        avg_rating=Avg('ratings__rating'),
        ratings_count=Count('ratings'),
        programs_count=Count('faculties__programs', distinct=True)
    ).order_by('name')
    
    # Пагинация
    paginator = Paginator(universities, 24)  # 24 университета на странице
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Обработка POST запроса для сравнения
    selected_ids = []
    if request.method == 'POST':
        selected_ids_str = request.POST.getlist('selected_universities')
        if selected_ids_str:
            try:
                selected_ids = [int(id) for id in selected_ids_str]
                if len(selected_ids) < 2:
                    messages.error(request, 'Выберите минимум 2 университета для сравнения.')
                elif len(selected_ids) > 5:
                    messages.error(request, 'Можно выбрать максимум 5 университетов для сравнения.')
                else:
                    university_ids = ','.join(str(id) for id in selected_ids)
                    return redirect('universities:compare_universities', university_ids=university_ids)
            except ValueError:
                messages.error(request, 'Ошибка в выбранных университетах.')
    
    # Получаем уникальные города для автодополнения
    cities = University.objects.values_list('city', flat=True).distinct().order_by('city')
    
    # Преобразуем selected_ids в set для быстрой проверки
    selected_ids_set = set(selected_ids)
    
    context = {
        'universities': page_obj,
        'page_obj': page_obj,
        'search_form': search_form,
        'selected_ids': selected_ids_set,
        'cities': cities,
        'selected_count': len(selected_ids),
    }
    return render(request, 'universities/comparison.html', context)


def compare_universities_view(request, university_ids):
    """Страница сравнения университетов"""
    try:
        ids = [int(id) for id in university_ids.split(',')]
        universities = University.objects.filter(id__in=ids).annotate(
            avg_rating=Avg('ratings__rating'),
            ratings_count=Count('ratings')
        )
        
        if len(universities) < 2:
            messages.error(request, 'Недостаточно университетов для сравнения.')
            return redirect('universities:comparison')
        
        # Получаем факультеты для каждого университета
        faculties_data = {}
        for university in universities:
            faculties_data[university.id] = Faculty.objects.filter(university=university)
        
        context = {
            'universities': universities,
            'faculties_data': faculties_data,
        }
        return render(request, 'universities/compare_universities.html', context)
    
    except (ValueError, University.DoesNotExist):
        messages.error(request, 'Ошибка в параметрах сравнения.')
        return redirect('universities:comparison')


def rating_leaderboard_view(request):
    """Рейтинг университетов"""
    universities = University.objects.annotate(
        avg_rating=Avg('ratings__rating'),
        ratings_count=Count('ratings')
    ).filter(ratings_count__gte=1).order_by('-avg_rating', '-ratings_count')
    
    # Пагинация
    paginator = Paginator(universities, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'universities': page_obj,
    }
    return render(request, 'universities/rating_leaderboard.html', context)


@login_required
def create_news_view(request, university_id):
    """Создание новости для университета"""
    university = get_object_or_404(University, id=university_id)
    
    if request.method == 'POST':
        form = NewsForm(request.POST, request.FILES)
        if form.is_valid():
            news = News(
                title=form.cleaned_data['title'],
                content=form.cleaned_data['content'],
                university=university,
                author=request.user,
                image=form.cleaned_data.get('image')
            )
            news.save()
            messages.success(request, 'Новость успешно создана!')
            return redirect('universities:university_detail', university_id=university_id)
    else:
        form = NewsForm()
    
    context = {
        'university': university,
        'form': form,
    }
    return render(request, 'universities/create_news.html', context)


def news_list_view(request):
    """Список всех новостей"""
    news = News.objects.filter(is_published=True).order_by('-created_at')
    
    # Пагинация
    paginator = Paginator(news, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'news': page_obj,
    }
    return render(request, 'universities/news_list.html', context)


def news_detail_view(request, news_id):
    """Детальная страница новости"""
    news = get_object_or_404(News, id=news_id, is_published=True)
    
    context = {
        'news': news,
    }
    return render(request, 'universities/news_detail.html', context)


def is_university_representative(user, university):
    """Проверяет, является ли пользователь одобренным представителем университета"""
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    return UniversityRepresentative.objects.filter(
        user=user,
        university=university,
        is_approved=True
    ).exists()


@login_required
def become_representative_view(request):
    """Запрос на получение статуса представителя университета"""
    if request.method == 'POST':
        form = BecomeRepresentativeForm(request.POST)
        if form.is_valid():
            # Проверяем, не существует ли уже запрос для этого пользователя и университета
            university = form.cleaned_data['university']
            existing = UniversityRepresentative.objects.filter(
                user=request.user,
                university=university
            ).first()
            
            if existing:
                if existing.is_approved:
                    messages.info(request, f'Вы уже являетесь одобренным представителем {university.name}')
                    return redirect('universities:my_representatives')
                else:
                    messages.info(request, f'Ваш запрос на представительство {university.name} уже отправлен и ожидает одобрения администратора')
                    return redirect('universities:my_representatives')
            
            representative = form.save(commit=False)
            representative.user = request.user
            representative.is_approved = False  # Требуется одобрение админа
            representative.save()
            
            messages.success(
                request,
                f'Ваш запрос на представительство {university.name} отправлен. '
                'После одобрения администратором вы сможете редактировать информацию о вузе.'
            )
            return redirect('universities:my_representatives')
    else:
        form = BecomeRepresentativeForm()
    
    context = {
        'form': form,
    }
    return render(request, 'universities/become_representative.html', context)


@login_required
def my_representatives_view(request):
    """Список представительств пользователя"""
    representatives = UniversityRepresentative.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'representatives': representatives,
    }
    return render(request, 'universities/my_representatives.html', context)


@login_required
def edit_university_view(request, university_id):
    """Редактирование информации о вузе (только для одобренных представителей)"""
    university = get_object_or_404(University, id=university_id)
    
    # Проверяем права доступа
    if not is_university_representative(request.user, university):
        messages.error(
            request,
            'У вас нет прав для редактирования информации об этом университете. '
            'Подайте запрос на получение статуса представителя.'
        )
        return redirect('universities:university_detail', university_id=university_id)
    
    if request.method == 'POST':
        form = UniversityEditForm(request.POST, request.FILES, instance=university)
        if form.is_valid():
            form.save()
            messages.success(request, 'Информация о вузе успешно обновлена!')
            return redirect('universities:university_detail', university_id=university_id)
    else:
        form = UniversityEditForm(instance=university)
    
    context = {
        'form': form,
        'university': university,
    }
    return render(request, 'universities/edit_university.html', context)
