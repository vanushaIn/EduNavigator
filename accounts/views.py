from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import UserRegistrationForm, UserProfileForm, UserUpdateForm
from .models import UserProfile, FavoriteUniversity


def register_view(request):
    """Регистрация пользователя"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('universities:home')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    """Вход пользователя"""
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        from django.contrib.auth import authenticate
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Добро пожаловать!')
            return redirect('universities:home')
        else:
            messages.error(request, 'Неверное имя пользователя или пароль.')
    
    return render(request, 'accounts/login.html')


def logout_view(request):
    """Выход пользователя"""
    logout(request)
    messages.info(request, 'Вы вышли из системы.')
    return redirect('universities:home')


@login_required
def profile_view(request):
    """Профиль пользователя"""
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
    
    return render(request, 'accounts/profile.html', {'profile': profile})


@login_required
def edit_profile_view(request):
    """Редактирование профиля пользователя"""
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
    
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Профиль успешно обновлен!')
            return redirect('accounts:profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = UserProfileForm(instance=profile)
    
    return render(request, 'accounts/edit_profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
    })


@login_required
def favorites_view(request):
    """Избранные университеты пользователя"""
    favorites = FavoriteUniversity.objects.filter(user=request.user).select_related('university')
    return render(request, 'accounts/favorites.html', {'favorites': favorites})


@login_required
def add_to_favorites(request, university_id):
    """Добавить университет в избранное"""
    from universities.models import University
    try:
        university = University.objects.get(id=university_id)
        favorite, created = FavoriteUniversity.objects.get_or_create(
            user=request.user,
            university=university
        )
        if created:
            messages.success(request, f'{university.name} добавлен в избранное!')
        else:
            messages.info(request, f'{university.name} уже в избранном!')
    except University.DoesNotExist:
        messages.error(request, 'Университет не найден!')
    
    return redirect('universities:university_detail', university_id=university_id)


@login_required
def remove_from_favorites(request, university_id):
    """Удалить университет из избранного"""
    try:
        favorite = FavoriteUniversity.objects.get(user=request.user, university_id=university_id)
        university_name = favorite.university.name
        favorite.delete()
        messages.success(request, f'{university_name} удален из избранного!')
    except FavoriteUniversity.DoesNotExist:
        messages.error(request, 'Университет не найден в избранном!')
    
    return redirect('accounts:favorites')
