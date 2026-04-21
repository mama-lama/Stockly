from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


class RegisterUserForm(UserCreationForm):
    username = forms.CharField(label='Логин')
    email = forms.EmailField(label='Email')
    password1 = forms.CharField(label='Пароль', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Повтор пароля', widget=forms.PasswordInput)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'password1', 'password2')