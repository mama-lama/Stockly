from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main.urls')),
    path('products/', include('products.urls')),
    path('forecast/', include('forecasting.urls')),
    path('suppliers/', include('suppliers.urls')),
    path('', include('users.urls')),
]