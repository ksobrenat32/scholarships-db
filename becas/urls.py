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
from becas_sntsa import views

urlpatterns = [
    path('', views.home, name='home'),
    path('admin/', admin.site.urls),
    path('signup/', views.signup, name='signup'),
    path('signin/', views.signin, name='signin'),
    path('signout/', views.signout, name='signout'),
    path('becas/', views.becas, name='becas'),
    path('becas/create_trabajador/', views.create_trabajador, name='create_trabajador'),
    path('becas/create_becario/', views.create_becario, name='create_becario'),
    path('becas/create_solicitud_aprovechamiento/', views.create_solicitud_aprovechamiento, name='create_solicitud_aprovechamiento'),
    path('becas/create_solicitud_excelencia/', views.create_solicitud_excelencia, name='create_solicitud_excelencia'),
    path('becas/create_solicitud_especial/', views.create_solicitud_especial, name='create_solicitud_especial'),
    path('becas/ver_becarios/', views.ver_becarios, name='ver_becarios'),
    path('becas/ver_solicitudes/', views.ver_solicitudes, name='ver_solicitudes'),
    path('media/<path:file_path>/', views.download_file, name='download_file'),
]
