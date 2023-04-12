"""
URL configuration for TherapistGPT project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from therapy.views import chat
from django.views.generic.base import RedirectView
from django.contrib.staticfiles.storage import staticfiles_storage

urlpatterns = [
    path('', chat, name='chat'),  # This is the default page, so we'll just redirect to 'chat
    path("admin/", admin.site.urls),
    path("therapy/", include("therapy.urls")),
    re_path(r'^favicon\.ico$', RedirectView.as_view(url=staticfiles_storage.url('favicon.ico'))),

]
