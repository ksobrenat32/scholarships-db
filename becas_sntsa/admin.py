from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
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

class SolicitudAdmin(admin.ModelAdmin):
    search_fields = ['becario__curp', 'fecha_solicitud', 'becario__trabajador__username']
    list_display = ('__str__', 'get_trabajador')
    readonly_fields = ('get_trabajador',)

    def get_trabajador(self, obj):
        trabajador_user = obj.becario.trabajador
        try:
            trabajador = Trabajador.objects.get(usuario=trabajador_user)
            url = reverse('admin:becas_sntsa_trabajador_change', args=[trabajador.pk])
            return format_html('<a href="{}">{}</a>', url, trabajador_user.username)
        except Trabajador.DoesNotExist:
            return trabajador_user.username
    get_trabajador.short_description = 'Trabajador'

class SolicitudAprovechamientoAdmin(SolicitudAdmin):
    pass

class SolicitudExcelenciaAdmin(SolicitudAdmin):
    pass

class SolicitudEspecialAdmin(SolicitudAdmin):
    pass

admin.site.register(Trabajador, TrabajadorAdmin)
admin.site.register(Becario, BecarioAdmin)
admin.site.register(SolicitudAprovechamiento, SolicitudAprovechamientoAdmin)
admin.site.register(SolicitudExcelencia, SolicitudExcelenciaAdmin)
admin.site.register(SolicitudEspecial, SolicitudEspecialAdmin)
