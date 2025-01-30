from django import forms
from django.forms import ModelForm
from main.models import Trabajador, Becario

class TrabajadorCreateForm(ModelForm):
    class Meta:
        model = Trabajador
        fields = ['nombre', 'apellido_paterno', 'apellido_materno', 'curp_archivo', 'telefono', 'correo', 'seccion', 'puesto', 'lugar_adscripcion']
        widgets = {
            'correo': forms.EmailInput(),
        }

class BecarioCreateForm(ModelForm):
    class Meta:
        model = Becario
        fields = ['nombre', 'apellido_paterno', 'apellido_materno', 'curp', 'curp_archivo', 'acta_nacimiento']
