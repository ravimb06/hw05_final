from django.views.generic import CreateView
from django import forms

from django.urls import reverse_lazy

from .forms import CreationForm


class SignUp(CreateView):
    form_class = CreationForm
    # После успешной регистрации перенаправляем пользователя на главную.
    success_url = reverse_lazy('posts:index')
    template_name = 'users/signup.html'


class LogOut(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy('post:index')
    template_name = 'users/logout.html'


class PasswordChange(forms.Form):
    old_password = forms.CharField(label='Введите текущий пароль')
    new_password = forms.CharField(label='Введите новый пароль')
    new_password_again = forms.CharField(
        label='Введите новый пароль (повторно)'
    )
    success_url = reverse_lazy('users:password_change_done')
    template_name = 'users/password_change_form.html'


class PasswordReset(forms.Form):
    email = forms.EmailField(label='Адрес электронной почты')
    success_url = reverse_lazy('users:password_reset_done')
    template_name = 'users/password_reset_form.html'


class PasswordResetComplete(forms.Form):
    new_password = forms.CharField(label='Введите новый пароль')
    new_password_again = forms.CharField(
        label='Введите новый пароль (повторно)'
    )
    success_url = reverse_lazy('users:password_reset_complete')
    template_name = 'users/password_reset_confirm.html'
