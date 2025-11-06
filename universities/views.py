from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Avg, Count
from django.http import JsonResponse
from .models import University, UniversityRating, UniversityComparison, Region, UniversityType, News, Faculty, Program
from .forms import UniversitySearchForm, UniversityRatingForm, UniversityComparisonForm, NewsForm
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
        university_type = form.cleaned_data.get('university_type')
        is_public = form.cleaned_data.get('is_public')
        min_rating = form.cleaned_data.get('min_rating')
        
        if name:
            universities = universities.filter(name__icontains=name)
        if region:
            universities = universities.filter(region=region)
        if university_type:
            universities = universities.filter(university_type=university_type)
        if is_public:
            universities = universities.filter(is_public=True)
        if min_rating:
            universities = universities.annotate(
                avg_rating=Avg('ratings__rating')
            ).filter(avg_rating__gte=min_rating)
    
    # Добавляем средний рейтинг
    universities = universities.annotate(
        avg_rating=Avg('ratings__rating'),
        ratings_count=Count('ratings')
    ).order_by('-avg_rating', 'name')
    
    # Пагинация
    paginator = Paginator(universities, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'form': form,
        'page_obj': page_obj,
        'universities': page_obj,
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
    
    context = {
        'university': university,
        'is_favorite': is_favorite,
        'ratings': ratings,
        'rating_stats': rating_stats,
        'faculties': faculties,
        'programs': programs,
        'news': news,
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
    if request.method == 'POST':
        form = UniversityComparisonForm(request.POST)
        if form.is_valid():
            universities = form.cleaned_data['universities']
            # Создаем URL для сравнения с параметрами
            university_ids = ','.join(str(u.id) for u in universities)
            return redirect('universities:compare_universities', university_ids=university_ids)
    else:
        form = UniversityComparisonForm()
    
    return render(request, 'universities/comparison.html', {'form': form})


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
