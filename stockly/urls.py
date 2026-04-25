from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.main.urls')),
    path('products/', include('apps.products.urls')),
    path('forecast/', include('apps.forecasting.urls')),
    path('suppliers/', include('apps.suppliers.urls')),
    path('', include('apps.users.urls')),
    path('application/', include('apps.application.urls')),
    path('imports/', include('apps.imports.urls')),
]
