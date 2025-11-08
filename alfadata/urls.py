from django.urls import path
from . import views

app_name = 'alfadata'

urlpatterns = [
    path('', views.upload_file, name='upload'),
    path('visualize/', views.visualize, name='visualize'),
]
