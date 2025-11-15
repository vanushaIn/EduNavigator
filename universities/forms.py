from django import forms
from .models import University, UniversityRating, UniversityComparison, Region, UniversityType, UniversityRepresentative


class UniversitySearchForm(forms.Form):
    """Форма поиска университетов"""
    name = forms.CharField(
        max_length=200,
        required=False,
        label="Название университета",
        widget=forms.TextInput(attrs={'placeholder': 'Введите название университета', 'class': 'form-control'})
    )
    region = forms.ModelChoiceField(
        queryset=Region.objects.all().order_by('name'),
        required=False,
        empty_label="Все регионы",
        label="Регион",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    city = forms.CharField(
        max_length=100,
        required=False,
        label="Город",
        widget=forms.TextInput(attrs={'placeholder': 'Введите город', 'class': 'form-control', 'list': 'cities-list'})
    )
    university_type = forms.ModelChoiceField(
        queryset=UniversityType.objects.all().order_by('name'),
        required=False,
        empty_label="Все типы",
        label="Тип университета",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    is_public = forms.BooleanField(
        required=False,
        label="Только государственные",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    min_rating = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=5,
        label="Минимальный рейтинг",
        widget=forms.NumberInput(attrs={'min': 1, 'max': 5, 'class': 'form-control'})
    )
    min_programs = forms.IntegerField(
        required=False,
        min_value=0,
        label="Минимум программ",
        widget=forms.NumberInput(attrs={'min': 0, 'class': 'form-control', 'placeholder': '0'})
    )
    max_tuition = forms.IntegerField(
        required=False,
        min_value=0,
        label="Максимальная стоимость (руб/год)",
        widget=forms.NumberInput(attrs={'min': 0, 'class': 'form-control', 'placeholder': 'Любая'})
    )


class UniversityRatingForm(forms.ModelForm):
    """Форма оценки университета"""
    
    class Meta:
        model = UniversityRating
        fields = ['rating', 'comment']
        labels = {
            'rating': 'Оценка',
            'comment': 'Комментарий',
        }
        widgets = {
            'rating': forms.Select(choices=[(i, i) for i in range(1, 6)]),
            'comment': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Оставьте свой отзыв о университете...'}),
        }


class UniversityComparisonForm(forms.ModelForm):
    """Форма сравнения университетов"""
    universities = forms.ModelMultipleChoiceField(
        queryset=University.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label="Выберите университеты для сравнения (максимум 5)"
    )
    
    class Meta:
        model = UniversityComparison
        fields = ['universities']
    
    def clean_universities(self):
        universities = self.cleaned_data['universities']
        if len(universities) > 5:
            raise forms.ValidationError("Можно выбрать максимум 5 университетов для сравнения.")
        if len(universities) < 2:
            raise forms.ValidationError("Выберите минимум 2 университета для сравнения.")
        return universities


class NewsForm(forms.Form):
    """Форма создания новости"""
    title = forms.CharField(max_length=200, label="Заголовок")
    content = forms.CharField(widget=forms.Textarea(attrs={'rows': 10}), label="Содержание")
    image = forms.ImageField(required=False, label="Изображение")


class UniversityEditForm(forms.ModelForm):
    """Форма редактирования информации о вузе (для представителей)"""
    
    class Meta:
        model = University
        fields = [
            'name', 'short_name', 'description', 'founded_year',
            'region', 'city', 'address',
            'website', 'email', 'phone',
            'logo', 'university_type', 'is_public',
            'accreditation', 'license'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'short_name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'founded_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'region': forms.Select(attrs={'class': 'form-select'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'university_type': forms.Select(attrs={'class': 'form-select'}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'accreditation': forms.TextInput(attrs={'class': 'form-control'}),
            'license': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'name': 'Название',
            'short_name': 'Краткое название',
            'description': 'Описание',
            'founded_year': 'Год основания',
            'region': 'Регион',
            'city': 'Город',
            'address': 'Адрес',
            'website': 'Официальный сайт',
            'email': 'Email',
            'phone': 'Телефон',
            'logo': 'Логотип',
            'university_type': 'Тип университета',
            'is_public': 'Государственный',
            'accreditation': 'Аккредитация',
            'license': 'Лицензия',
        }


class BecomeRepresentativeForm(forms.ModelForm):
    """Форма для запроса на получение статуса представителя"""
    
    class Meta:
        model = UniversityRepresentative
        fields = ['university', 'position', 'phone']
        widgets = {
            'university': forms.Select(attrs={'class': 'form-select'}),
            'position': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Например: Директор по маркетингу'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+7 (XXX) XXX-XX-XX'}),
        }
        labels = {
            'university': 'Университет',
            'position': 'Должность',
            'phone': 'Контактный телефон',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['university'].queryset = University.objects.all().order_by('name')
