from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class Region(models.Model):
    """Регион РФ"""
    name = models.CharField(max_length=100, verbose_name="Название региона")
    code = models.CharField(max_length=10, unique=True, verbose_name="Код региона")
    
    class Meta:
        verbose_name = "Регион"
        verbose_name_plural = "Регионы"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class UniversityType(models.Model):
    """Тип университета"""
    name = models.CharField(max_length=50, verbose_name="Тип")
    
    class Meta:
        verbose_name = "Тип университета"
        verbose_name_plural = "Типы университетов"
    
    def __str__(self):
        return self.name


class University(models.Model):
    """Университет"""
    name = models.CharField(max_length=200, verbose_name="Название")
    short_name = models.CharField(max_length=50, verbose_name="Краткое название")
    description = models.TextField(verbose_name="Описание")
    founded_year = models.PositiveIntegerField(verbose_name="Год основания")
    region = models.ForeignKey(Region, on_delete=models.CASCADE, verbose_name="Регион")
    city = models.CharField(max_length=100, verbose_name="Город")
    address = models.TextField(verbose_name="Адрес")
    website = models.URLField(blank=True, verbose_name="Официальный сайт")
    email = models.EmailField(blank=True, verbose_name="Email")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")
    logo = models.ImageField(upload_to='university_logos/', blank=True, null=True, verbose_name="Логотип")
    university_type = models.ForeignKey(UniversityType, on_delete=models.CASCADE, verbose_name="Тип")
    is_public = models.BooleanField(default=True, verbose_name="Государственный")
    accreditation = models.CharField(max_length=100, blank=True, verbose_name="Аккредитация")
    license = models.CharField(max_length=100, blank=True, verbose_name="Лицензия")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Университет"
        verbose_name_plural = "Университеты"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    @property
    def average_rating(self):
        """Средний рейтинг университета"""
        ratings = self.ratings.all()
        if ratings.exists():
            return sum(rating.rating for rating in ratings) / ratings.count()
        return 0


class Faculty(models.Model):
    """Факультет"""
    name = models.CharField(max_length=200, verbose_name="Название факультета")
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name='faculties', verbose_name="Университет")
    description = models.TextField(blank=True, verbose_name="Описание")
    dean = models.CharField(max_length=100, blank=True, verbose_name="Декан")
    
    class Meta:
        verbose_name = "Факультет"
        verbose_name_plural = "Факультеты"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.university.short_name})"


class Program(models.Model):
    """Образовательная программа"""
    name = models.CharField(max_length=200, verbose_name="Название программы")
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='programs', verbose_name="Факультет")
    degree_level = models.CharField(max_length=50, verbose_name="Уровень образования")
    duration_years = models.PositiveIntegerField(verbose_name="Срок обучения (лет)")
    description = models.TextField(blank=True, verbose_name="Описание")
    tuition_fee = models.PositiveIntegerField(blank=True, null=True, verbose_name="Стоимость обучения (руб/год)")
    
    class Meta:
        verbose_name = "Образовательная программа"
        verbose_name_plural = "Образовательные программы"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.faculty.university.short_name})"


class UniversityRating(models.Model):
    """Рейтинг университета"""
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name='ratings', verbose_name="Университет")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Оценка"
    )
    comment = models.TextField(blank=True, verbose_name="Комментарий")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Рейтинг университета"
        verbose_name_plural = "Рейтинги университетов"
        unique_together = ['university', 'user']
    
    def __str__(self):
        return f"{self.university.name} - {self.rating}/5"


class UniversityComparison(models.Model):
    """Сравнение университетов"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    universities = models.ManyToManyField(University, verbose_name="Университеты")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Сравнение университетов"
        verbose_name_plural = "Сравнения университетов"
    
    def __str__(self):
        return f"Сравнение {self.universities.count()} университетов"


class News(models.Model):
    """Новости университетов"""
    title = models.CharField(max_length=200, verbose_name="Заголовок")
    content = models.TextField(verbose_name="Содержание")
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name='news', verbose_name="Университет")
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор")
    image = models.ImageField(upload_to='news_images/', blank=True, null=True, verbose_name="Изображение")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=True, verbose_name="Опубликовано")
    
    class Meta:
        verbose_name = "Новость"
        verbose_name_plural = "Новости"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
