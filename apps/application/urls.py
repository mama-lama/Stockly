from django.urls import path
from . import views

urlpatterns = [
    path('', views.application_page, name='application'),
    path('export-excel/', views.export_excel, name='export_excel'),
]
