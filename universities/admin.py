from django.contrib import admin
from .models import (
    Region, UniversityType, University, Faculty, Program, 
    UniversityRating, UniversityComparison, News, UniversityRepresentative
)


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ['name', 'code']
    search_fields = ['name', 'code']
    ordering = ['name']


@admin.register(UniversityType)
class UniversityTypeAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    list_display = ['name', 'short_name', 'city', 'region', 'university_type', 'is_public', 'yandex_rating', 'google_rating']
    list_filter = ['region', 'university_type', 'is_public', 'founded_year']
    search_fields = ['name', 'short_name', 'city']
    list_editable = ['is_public']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'short_name', 'description', 'founded_year')
        }),
        ('Местоположение', {
            'fields': ('region', 'city', 'address')
        }),
        ('Контактная информация', {
            'fields': ('website', 'email', 'phone')
        }),
        ('Классификация', {
            'fields': ('university_type', 'is_public', 'accreditation', 'license')
        }),
        ('Рейтинг Яндекс Карт', {
            'fields': ('yandex_rating', 'yandex_reviews_count', 'yandex_place_id')
        }),
        ('Рейтинг Google', {
            'fields': ('google_rating', 'google_reviews_count', 'google_place_id')
        }),
        ('Медиа', {
            'fields': ('logo',)
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ['name', 'university', 'dean']
    list_filter = ['university']
    search_fields = ['name', 'dean']
    ordering = ['university', 'name']


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ['name', 'faculty', 'degree_level', 'duration_years', 'tuition_fee']
    list_filter = ['degree_level', 'duration_years', 'faculty__university']
    search_fields = ['name']
    ordering = ['faculty__university', 'name']


@admin.register(UniversityRating)
class UniversityRatingAdmin(admin.ModelAdmin):
    list_display = ['university', 'user', 'rating', 'created_at']
    list_filter = ['rating', 'created_at', 'university']
    search_fields = ['university__name', 'user__username', 'comment']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(UniversityComparison)
class UniversityComparisonAdmin(admin.ModelAdmin):
    list_display = ['user', 'universities_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    def universities_count(self, obj):
        return obj.universities.count()
    universities_count.short_description = 'Количество университетов'


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ['title', 'university', 'author', 'is_published', 'created_at']
    list_filter = ['is_published', 'created_at', 'university']
    search_fields = ['title', 'content', 'university__name']
    list_editable = ['is_published']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'content', 'university', 'author')
        }),
        ('Медиа', {
            'fields': ('image',)
        }),
        ('Публикация', {
            'fields': ('is_published',)
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(UniversityRepresentative)
class UniversityRepresentativeAdmin(admin.ModelAdmin):
    list_display = ['user', 'university', 'is_approved', 'position', 'created_at']
    list_filter = ['is_approved', 'created_at', 'university']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'university__name', 'position']
    list_editable = ['is_approved']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'university', 'is_approved')
        }),
        ('Контактная информация', {
            'fields': ('position', 'phone')
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_representatives', 'disapprove_representatives']
    
    def approve_representatives(self, request, queryset):
        """Одобрить выбранных представителей"""
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'Одобрено {updated} представителей.')
    approve_representatives.short_description = 'Одобрить выбранных представителей'
    
    def disapprove_representatives(self, request, queryset):
        """Отклонить выбранных представителей"""
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'Отклонено {updated} представителей.')
    disapprove_representatives.short_description = 'Отклонить выбранных представителей'
