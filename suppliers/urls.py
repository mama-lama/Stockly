from django.urls import path
from . import views

urlpatterns = [
    path('', views.suppliers_page, name='suppliers'),
]