from django.contrib import admin
from .models import UserProfile, FavoriteUniversity


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'city', 'created_at']
    list_filter = ['city', 'created_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'phone', 'city']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Пользователь', {
            'fields': ('user',)
        }),
        ('Личная информация', {
            'fields': ('avatar', 'phone', 'birth_date', 'city', 'bio')
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(FavoriteUniversity)
class FavoriteUniversityAdmin(admin.ModelAdmin):
    list_display = ['user', 'university', 'created_at']
    list_filter = ['created_at', 'university__region']
    search_fields = ['user__username', 'university__name']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
