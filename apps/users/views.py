from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView

from .forms import RegisterUserForm


MENU = [
    {'title': 'Главная', 'url': '/'},
    {'title': 'Товары', 'url': '/products/'},
    {'title': 'Прогноз', 'url': '/forecast/'},
    {'title': 'Поставщики', 'url': '/suppliers/'},
    {'title': 'Заявка', 'url': '/application/'},
    {'title': 'Импорт', 'url': '/imports/'},
]



class RegisterUser(CreateView):
    form_class = RegisterUserForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('profile')

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu'] = MENU
        context['title'] = 'Регистрация'
        return context


class LogoutUser(LogoutView):
    next_page = reverse_lazy('home')


class LoginUser(LoginView):
    template_name = 'users/login.html'

    def get_success_url(self):
        return reverse_lazy('profile')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu'] = MENU
        context['title'] = 'Вход'
        return context


class ProfileUser(LoginRequiredMixin, TemplateView):
    template_name = 'users/profile.html'
    login_url = '/register/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu'] = MENU
        context['title'] = 'Профиль'
        return context