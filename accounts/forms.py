from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile


class UserRegistrationForm(UserCreationForm):
    """Форма регистрации пользователя"""
    email = forms.EmailField(required=True, label="Email")
    first_name = forms.CharField(max_length=30, required=True, label="Имя")
    last_name = forms.CharField(max_length=30, required=True, label="Фамилия")
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
        labels = {
            'username': 'Имя пользователя',
            'password1': 'Пароль',
            'password2': 'Подтверждение пароля',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].help_text = 'Обязательное поле. 150 символов или меньше. Только буквы, цифры и @/./+/-/_'
        self.fields['password1'].help_text = 'Пароль должен содержать минимум 8 символов'
        self.fields['password2'].help_text = 'Введите тот же пароль для подтверждения'
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            UserProfile.objects.create(user=user)
        return user


class UserProfileForm(forms.ModelForm):
    """Форма редактирования профиля пользователя"""
    
    class Meta:
        model = UserProfile
        fields = ['avatar', 'phone', 'birth_date', 'city', 'bio']
        labels = {
            'avatar': 'Аватар',
            'phone': 'Телефон',
            'birth_date': 'Дата рождения',
            'city': 'Город',
            'bio': 'О себе',
        }
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'bio': forms.Textarea(attrs={'rows': 4}),
        }


class UserUpdateForm(forms.ModelForm):
    """Форма обновления данных пользователя"""
    email = forms.EmailField(required=True, label="Email")
    first_name = forms.CharField(max_length=30, required=True, label="Имя")
    last_name = forms.CharField(max_length=30, required=True, label="Фамилия")
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        labels = {
            'username': 'Имя пользователя',
        }
