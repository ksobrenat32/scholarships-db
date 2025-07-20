from django.contrib import admin
from becas_sntsa.models import Seccion, Puesto, LugarAdscripcion, Grado, Trabajador, Becario, SolicitudAprovechamiento, SolicitudExcelencia, SolicitudEspecial

# Register your models here.

# Registra los modelos en el administrador de Django
admin.site.register(Seccion)
admin.site.register(Puesto)
admin.site.register(LugarAdscripcion)
admin.site.register(Grado)

class TrabajadorAdmin(admin.ModelAdmin):
    search_fields = ['usuario__username']  # Search by username of linked user
    list_filter = ['aprobado', 'lugar_adscripcion', 'jurisdiccion']

class BecarioAdmin(admin.ModelAdmin):
    search_fields = ['curp']  # Search by curp

class SolicitudAprovechamientoAdmin(admin.ModelAdmin):
    search_fields = ['becario__curp', 'fecha_solicitud']  # Search by becario or fecha_solicitud

class SolicitudExcelenciaAdmin(admin.ModelAdmin):
    search_fields = ['becario__curp', 'fecha_solicitud']  # Search by becario or fecha_solicitud

class SolicitudEspecialAdmin(admin.ModelAdmin):
    search_fields = ['becario__curp', 'fecha_solicitud']  # Search by becario or fecha_solicitud

admin.site.register(Trabajador, TrabajadorAdmin)
admin.site.register(Becario, BecarioAdmin)
admin.site.register(SolicitudAprovechamiento, SolicitudAprovechamientoAdmin)
admin.site.register(SolicitudExcelencia, SolicitudExcelenciaAdmin)
admin.site.register(SolicitudEspecial, SolicitudEspecialAdmin)
