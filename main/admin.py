from django.contrib import admin
from main.models import Seccion, Puesto, LugarAdscripcion, Grado, Trabajador, Becario, Solicitud, SolicitudNormal, SolicitudEspecial

# Register your models here.

# Registra los modelos en el administrador de Django
admin.site.register(Seccion)
admin.site.register(Puesto)
admin.site.register(LugarAdscripcion)
admin.site.register(Grado)

class TrabajadorAdmin(admin.ModelAdmin):
    search_fields = ['usuario__username']  # Search by username of linked user

class BecarioAdmin(admin.ModelAdmin):
    search_fields = ['curp']  # Search by curp

class SolicitudNormalAdmin(admin.ModelAdmin):
    search_fields = ['becario__curp', 'fecha_solicitud']  # Search by becario or fecha_solicitud

class SolicitudEspecialAdmin(admin.ModelAdmin):
    search_fields = ['becario__curp', 'fecha_solicitud']  # Search by becario or fecha_solicitud

admin.site.register(Trabajador, TrabajadorAdmin)
admin.site.register(Becario, BecarioAdmin)
admin.site.register(SolicitudNormal, SolicitudNormalAdmin)
admin.site.register(SolicitudEspecial, SolicitudEspecialAdmin)
