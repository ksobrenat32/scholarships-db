"""
Forms for the becas_sntsa app.

This file defines the forms used to create and edit workers, scholars, and scholarship applications.
"""
import re
from django import forms
from django.forms import ModelForm
from django.core.exceptions import ValidationError
from becas_sntsa.models import Trabajador, Becario, SolicitudAprovechamiento, SolicitudExcelencia, SolicitudEspecial

def validar_curp(curp):
    """
    Valida el formato de la CURP.
    """
    regex = r"^[A-Z]{1}[AEIOU]{1}[A-Z]{2}[0-9]{2}(0[1-9]|1[0-2])(0[1-9]|1[0-9]|2[0-9]|3[0-1])[HM]{1}(AS|BC|BS|CC|CS|CH|CL|CM|DF|DG|GT|GR|HG|JC|MC|MN|MS|NT|NL|OC|PL|QT|QR|SP|SL|SR|TC|TS|TL|VZ|YN|ZS|NE)[A-Z]{3}[A-Z0-9]{1}[0-9]{1}$"
    if not re.match(regex, curp):
        raise ValidationError('El formato de la CURP no es válido.')

class TrabajadorCreateForm(ModelForm):
    """
    A form for creating a new worker.
    """
    class Meta:
        """
        Meta options for the TrabajadorCreateForm.
        """
        model = Trabajador
        fields = ['nombre', 'apellido_paterno', 'apellido_materno', 'talon_pago_archivo',
                  'telefono', 'correo', 'seccion', 'puesto', 'jurisdiccion', 'lugar_adscripcion']
        widgets = {
            'correo': forms.EmailInput(),
        }


class BecarioCreateForm(ModelForm):
    """
    A form for creating a new scholar.
    """
    class Meta:
        """
        Meta options for the BecarioCreateForm.
        """
        model = Becario
        fields = ['nombre', 'apellido_paterno', 'apellido_materno',
                  'curp', 'curp_archivo', 'acta_nacimiento']
        widgets = {
            'curp': forms.TextInput(attrs={
                'pattern': r'^[A-Z]{1}[AEIOU]{1}[A-Z]{2}[0-9]{2}(0[1-9]|1[0-2])(0[1-9]|1[0-9]|2[0-9]|3[0-1])[HM]{1}(AS|BC|BS|CC|CS|CH|CL|CM|DF|DG|GT|GR|HG|JC|MC|MN|MS|NT|NL|OC|PL|QT|QR|SP|SL|SR|TC|TS|TL|VZ|YN|ZS|NE)[A-Z]{3}[A-Z0-9]{1}[0-9]{1}$',
                'title': 'Ingrese un formato de CURP válido de 18 caracteres'
            })
        }

    def clean_curp(self):
        curp = self.cleaned_data.get('curp')
        if curp:
            curp = curp.upper()
            validar_curp(curp)
        return curp


class TrabajadorEditForm(ModelForm):
    """
    A form for editing an existing worker.
    """
    class Meta:
        """
        Meta options for the TrabajadorEditForm.
        """
        model = Trabajador
        fields = ['talon_pago_archivo', 'telefono', 'correo']
        widgets = {
            'correo': forms.EmailInput(),
        }


class BecarioEditForm(ModelForm):
    """
    A form for editing an existing scholar.
    """
    class Meta:
        """
        Meta options for the BecarioEditForm.
        """
        model = Becario
        fields = ['nombre', 'apellido_paterno', 'apellido_materno',
                  'curp', 'curp_archivo', 'acta_nacimiento']
        widgets = {
            'curp': forms.TextInput(attrs={
                'pattern': r'^[A-Z]{1}[AEIOU]{1}[A-Z]{2}[0-9]{2}(0[1-9]|1[0-2])(0[1-9]|1[0-9]|2[0-9]|3[0-1])[HM]{1}(AS|BC|BS|CC|CS|CH|CL|CM|DF|DG|GT|GR|HG|JC|MC|MN|MS|NT|NL|OC|PL|QT|QR|SP|SL|SR|TC|TS|TL|VZ|YN|ZS|NE)[A-Z]{3}[A-Z0-9]{1}[0-9]{1}$',
                'title': 'Ingrese un formato de CURP válido de 18 caracteres'
            })
        }

    def clean_curp(self):
        curp = self.cleaned_data.get('curp')
        if curp:
            curp = curp.upper()
            validar_curp(curp)
        return curp


class SolicitudAprovechamientoCreateForm(forms.ModelForm):
    """
    A form for creating a new scholarship application for academic achievement.
    """
    becario = forms.ModelChoiceField(queryset=Becario.objects.none())

    class Meta:
        """
        Meta options for the SolicitudAprovechamientoCreateForm.
        """
        model = SolicitudAprovechamiento
        fields = ['becario', 'grado', 'promedio',
                  'boleta', 'recibo_nomina', 'ine']

    def __init__(self, *args, **kwargs):
        """
        Initializes the form and filters the 'becario' queryset to only include
        scholars associated with the current user.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        user = kwargs.pop('user')
        super(SolicitudAprovechamientoCreateForm, self).__init__(*args, **kwargs)
        self.fields['becario'].queryset = Becario.objects.filter(
            trabajador=user)

    def clean_promedio(self):
        """
        Validates that the 'promedio' field is between 6.0 and 10.0.

        Returns:
            float: The cleaned 'promedio' value.

        Raises:
            forms.ValidationError: If the 'promedio' is not within the valid range.
        """
        promedio = self.cleaned_data.get('promedio')
        if promedio < 6.0 or promedio > 10.0:
            raise forms.ValidationError(
                'El promedio debe estar entre 6.0 y 10.0')
        return promedio


class SolicitudExcelenciaCreateForm(forms.ModelForm):
    """
    A form for creating a new scholarship application for academic excellence.
    """
    becario = forms.ModelChoiceField(queryset=Becario.objects.none())

    class Meta:
        """
        Meta options for the SolicitudExcelenciaCreateForm.
        """
        model = SolicitudExcelencia
        fields = ['becario', 'grado', 'promedio',
                  'boleta', 'recibo_nomina', 'ine', 'carrera']

    def __init__(self, *args, **kwargs):
        """
        Initializes the form and filters the 'becario' queryset to only include
        scholars associated with the current user.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        user = kwargs.pop('user')
        super(SolicitudExcelenciaCreateForm, self).__init__(*args, **kwargs)
        self.fields['becario'].queryset = Becario.objects.filter(
            trabajador=user)

    def clean_promedio(self):
        """
        Validates that the 'promedio' field is between 6.0 and 10.0.

        Returns:
            float: The cleaned 'promedio' value.

        Raises:
            forms.ValidationError: If the 'promedio' is not within the valid range.
        """
        promedio = self.cleaned_data.get('promedio')
        if promedio < 6.0 or promedio > 10.0:
            raise forms.ValidationError(
                'El promedio debe estar entre 6.0 y 10.0')
        return promedio


class SolicitudEspecialCreateForm(forms.ModelForm):
    """
    A form for creating a new special scholarship application.
    """
    becario = forms.ModelChoiceField(queryset=Becario.objects.none())

    class Meta:
        """
        Meta options for the SolicitudEspecialCreateForm.
        """
        model = SolicitudEspecial
        fields = ['becario', 'diagnostico_medico', 'tipo_educacion',
                  'certificado_medico', 'certificado_escolar', 'recibo_nomina', 'ine']

    def __init__(self, *args, **kwargs):
        """
        Initializes the form and filters the 'becario' queryset to only include
        scholars associated with the current user.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        user = kwargs.pop('user')
        super(SolicitudEspecialCreateForm, self).__init__(*args, **kwargs)
        self.fields['becario'].queryset = Becario.objects.filter(
            trabajador=user)
