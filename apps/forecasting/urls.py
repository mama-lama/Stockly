from django.urls import path
from . import views

urlpatterns = [
    path('', views.forecast_page, name='forecast_page'),
]