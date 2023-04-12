from django.urls import path
from .import views

urlpatterns = [
    path('', views.home, name='home'),
    path('chat/', views.chat, name='chat'),
    path('api-message/', views.api_message, name='api_message'),
    path('update-api-key/', views.update_api_key, name='update_api_key'),
    path('update-model/', views.update_model, name='update_model'),
    path('download-data/', views.download_data, name='download_data'),
]

