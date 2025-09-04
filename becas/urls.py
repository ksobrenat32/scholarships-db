"""
URL configuration for the becas project.

This file defines the URL patterns for the entire project. It maps URLs to
views, allowing the Django framework to route requests to the appropriate
view function.
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
    path('becas/editar_usuario/', views.editar_usuario, name='editar_usuario'),
    path('becas/editar_becario/<int:becario_id>/', views.editar_becario, name='editar_becario'),
    path('media/<path:file_path>/', views.download_file, name='download_file'),
]
