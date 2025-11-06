from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    """Профиль пользователя"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name="Аватар")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")
    birth_date = models.DateField(blank=True, null=True, verbose_name="Дата рождения")
    city = models.CharField(max_length=100, blank=True, verbose_name="Город")
    bio = models.TextField(blank=True, verbose_name="О себе")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"
    
    def __str__(self):
        return f"Профиль {self.user.username}"


class FavoriteUniversity(models.Model):
    """Избранные университеты пользователя"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    university = models.ForeignKey('universities.University', on_delete=models.CASCADE, verbose_name="Университет")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Избранный университет"
        verbose_name_plural = "Избранные университеты"
        unique_together = ['user', 'university']
    
    def __str__(self):
        return f"{self.user.username} - {self.university.name}"
