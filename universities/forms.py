from django import forms
from .models import University, UniversityRating, UniversityComparison, Region, UniversityType


class UniversitySearchForm(forms.Form):
    """Форма поиска университетов"""
    name = forms.CharField(
        max_length=200,
        required=False,
        label="Название университета",
        widget=forms.TextInput(attrs={'placeholder': 'Введите название университета'})
    )
    region = forms.ModelChoiceField(
        queryset=Region.objects.all(),
        required=False,
        empty_label="Все регионы",
        label="Регион"
    )
    university_type = forms.ModelChoiceField(
        queryset=UniversityType.objects.all(),
        required=False,
        empty_label="Все типы",
        label="Тип университета"
    )
    is_public = forms.BooleanField(
        required=False,
        label="Только государственные"
    )
    min_rating = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=5,
        label="Минимальный рейтинг",
        widget=forms.NumberInput(attrs={'min': 1, 'max': 5})
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
