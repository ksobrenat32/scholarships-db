from django import forms
from django.forms import ModelForm
from main.models import Usuario, Trabajador, Becario

class UsuarioCreateForm(ModelForm):
    class Meta:
        model = Usuario
        fields = '__all__'

class TrabajadorCreateForm(ModelForm):
    class Meta:
        model = Trabajador
        fields = 'telefono', 'correo', 'seccion', 'puesto', 'lugar_adscripcion'
        widgets = {
            'correo': forms.EmailInput(),
        }

class BecarioCreateForm(ModelForm):
    class Meta:
        model = Becario
        fields = ['sexo', 'fecha_nacimiento', 'acta_nacimiento']
        widgets = {
            'sexo': forms.Select(choices=[('H', 'Hombre'), ('M', 'Mujer')]),
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
        }