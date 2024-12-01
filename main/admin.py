from django.contrib import admin
from main.models import Seccion, Puesto, LugarAdscripcion, Grado, Usuario, Trabajador, Becario, TrabajadorBecario, Solicitud, SolicitudEspecial

# Register your models here.

# Registra los modelos en el administrador de Django
admin.site.register(Seccion)
admin.site.register(Puesto)
admin.site.register(LugarAdscripcion)
admin.site.register(Grado)
admin.site.register(Usuario)
admin.site.register(Trabajador)
admin.site.register(Becario)
admin.site.register(TrabajadorBecario)
admin.site.register(Solicitud)
admin.site.register(SolicitudEspecial)
