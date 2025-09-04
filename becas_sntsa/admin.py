"""
Admin configurations for the becas_sntsa app.

This file defines how the models are displayed and managed in the Django admin interface.
"""
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from becas_sntsa.models import Seccion, Puesto, LugarAdscripcion, Grado, Trabajador, Becario, SolicitudAprovechamiento, SolicitudExcelencia, SolicitudEspecial


admin.site.register(Seccion)
admin.site.register(Puesto)
admin.site.register(LugarAdscripcion)
admin.site.register(Grado)


class TrabajadorAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Trabajador model.
    """
    search_fields = ['usuario__username']
    list_filter = ['aprobado', 'lugar_adscripcion', 'jurisdiccion']


class BecarioAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Becario model.
    """
    search_fields = ['curp']


class SolicitudAdmin(admin.ModelAdmin):
    """
    Base admin configuration for all Solicitud models.
    """
    search_fields = ['becario__curp',
                       'fecha_solicitud', 'becario__trabajador__username']
    list_display = ('__str__', 'get_trabajador')
    readonly_fields = ('get_trabajador',)

    def get_trabajador(self, obj):
        """
        Returns a link to the associated worker's admin page.

        Args:
            obj (Solicitud): The Solicitud instance.

        Returns:
            str: An HTML link to the worker's admin page or the worker's username.
        """
        trabajador_user = obj.becario.trabajador
        try:
            trabajador = Trabajador.objects.get(usuario=trabajador_user)
            url = reverse('admin:becas_sntsa_trabajador_change',
                          args=[trabajador.pk])
            return format_html('<a href="{}">{}</a>', url, trabajador_user.username)
        except Trabajador.DoesNotExist:
            return trabajador_user.username
    get_trabajador.short_description = 'Trabajador'


class SolicitudAprovechamientoAdmin(SolicitudAdmin):
    """
    Admin configuration for the SolicitudAprovechamiento model.
    """
    pass


class SolicitudExcelenciaAdmin(SolicitudAdmin):
    """
    Admin configuration for the SolicitudExcelencia model.
    """
    pass


class SolicitudEspecialAdmin(SolicitudAdmin):
    """
    Admin configuration for the SolicitudEspecial model.
    """
    pass


admin.site.register(Trabajador, TrabajadorAdmin)
admin.site.register(Becario, BecarioAdmin)
admin.site.register(SolicitudAprovechamiento, SolicitudAprovechamientoAdmin)
admin.site.register(SolicitudExcelencia, SolicitudExcelenciaAdmin)
admin.site.register(SolicitudEspecial, SolicitudEspecialAdmin)
