from django import forms
from django.forms import ModelForm
from becas_sntsa.models import Trabajador, Becario, SolicitudAprovechamiento, SolicitudExcelencia, SolicitudEspecial

class TrabajadorCreateForm(ModelForm):
    class Meta:
        model = Trabajador
        fields = ['nombre', 'apellido_paterno', 'apellido_materno', 'curp_archivo', 'telefono', 'correo', 'seccion', 'puesto', 'jurisdiccion', 'lugar_adscripcion']
        widgets = {
            'correo': forms.EmailInput(),
        }

class BecarioCreateForm(ModelForm):
    class Meta:
        model = Becario
        fields = ['nombre', 'apellido_paterno', 'apellido_materno', 'curp', 'curp_archivo', 'acta_nacimiento']

class SolicitudAprovechamientoCreateForm(forms.ModelForm):
    becario = forms.ModelChoiceField(queryset=Becario.objects.none())

    class Meta:
        model = SolicitudAprovechamiento
        fields = ['becario', 'grado', 'promedio', 'boleta', 'recibo_nomina', 'ine']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(SolicitudAprovechamientoCreateForm, self).__init__(*args, **kwargs)
        self.fields['becario'].queryset = Becario.objects.filter(trabajador=user)

    def clean_promedio(self):
        promedio = self.cleaned_data.get('promedio')
        if promedio < 6.0 or promedio > 10.0:
            raise forms.ValidationError('El promedio debe estar entre 6.0 y 10.0')
        return promedio

class SolicitudExcelenciaCreateForm(forms.ModelForm):
    becario = forms.ModelChoiceField(queryset=Becario.objects.none())

    class Meta:
        model = SolicitudExcelencia
        fields = ['becario', 'grado', 'promedio', 'boleta', 'recibo_nomina', 'ine', 'carrera']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(SolicitudExcelenciaCreateForm, self).__init__(*args, **kwargs)
        self.fields['becario'].queryset = Becario.objects.filter(trabajador=user)

    def clean_promedio(self):
        promedio = self.cleaned_data.get('promedio')
        if promedio < 6.0 or promedio > 10.0:
            raise forms.ValidationError('El promedio debe estar entre 6.0 y 10.0')
        return promedio

class SolicitudEspecialCreateForm(forms.ModelForm):
    becario = forms.ModelChoiceField(queryset=Becario.objects.none())

    class Meta:
        model = SolicitudEspecial
        fields = ['becario', 'diagnostico_medico', 'tipo_educacion', 'certificado_medico', 'certificado_escolar', 'recibo_nomina', 'ine']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(SolicitudEspecialCreateForm, self).__init__(*args, **kwargs)
        self.fields['becario'].queryset = Becario.objects.filter(trabajador=user)
