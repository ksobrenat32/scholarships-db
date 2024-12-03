"""
URL configuration for becas project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.urls import path
from main import views

urlpatterns = [
    path('', views.home, name='home'),
    path('admin/', admin.site.urls),
    path('signup/', views.signup, name='signup'),
    path('signin/', views.signin, name='signin'),
    path('signout/', views.signout, name='signout'),
    path('becas/', views.becas, name='becas'),
    path('becas/create_usuario/', views.create_usuario, name='create_usuario'),
    path('becas/create_trabajador/<str:curp>/', views.create_trabajador, name='create_trabajador'),
    path('becas/create_becario/<str:curp>/', views.create_becario, name='create_becario'),
    path('media/<path:file_path>/', views.download_file, name='download_file'),
]
