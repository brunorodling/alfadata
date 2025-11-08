from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('alfadata.urls')),  # delega para alfadata/urls.py
]
