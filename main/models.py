from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


# Create your models here.

# Clases para el modelo de la base de datos

# Clase para la seccion de trabajadores
class Seccion(models.Model):
    numero = models.IntegerField()

    def __str__(self):
        return str(self.numero)

# Clase para el puesto de los trabajadores
class Puesto(models.Model):
    clave = models.CharField(max_length=8)

    def __str__(self):
        return self.clave

# Clase para el lugar de adscripcion de los trabajadores
class LugarAdscripcion(models.Model):
    alias = models.CharField(max_length=32, null=True, blank=True)
    nombre = models.CharField(max_length=128)

    def __str__(self):
        return self.nombre

# Clase para el grado del becario
class Grado(models.Model):
    clave = models.CharField(max_length=4)
    nombre = models.CharField(max_length=64)

    def __str__(self):
        return "{} - {}".format(self.clave, self.nombre)

# Clase para el modelo de Usuario
class Usuario(models.Model):
    nombre = models.CharField(max_length=128)
    apellido_paterno = models.CharField(max_length=128)
    apellido_materno = models.CharField(max_length=128, null=True, blank=True)
    curp = models.CharField(max_length=18, unique=True)
    curp_archivo = models.FileField(upload_to='curp/')
    es_trabajador = models.BooleanField(default=False)
    es_becario = models.BooleanField(default=False)

    def clean(self):
        super().clean()
        if self.es_trabajador == False and self.es_becario == False:
            raise ValidationError("El usuario debe ser trabajador o becario o ambos")

    def __str__(self):
        return "{} {} {} {}".format(self.curp, self.nombre, self.apellido_paterno, self.apellido_materno)

# Clase para el modelo de Trabajador, hereda de Usuario
class Trabajador(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE)
    telefono = models.CharField(max_length=16)
    correo = models.EmailField()
    seccion = models.ForeignKey(Seccion, on_delete=models.CASCADE)
    puesto = models.ForeignKey(Puesto, on_delete=models.CASCADE)
    lugar_adscripcion = models.ForeignKey(LugarAdscripcion, on_delete=models.CASCADE)

    def __str__(self):
        return "{}".format(self.usuario)

# Clase para el modelo de Becario, hereda de Usuario
class Becario(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE)
    sexo = models.CharField(max_length=1)
    fecha_nacimiento = models.DateField()
    acta_nacimiento = models.FileField(upload_to='acta_nacimiento/')

    def __str__(self):
        return "{}".format(self.usuario)

# Clase para la relación trabajador-becario
class TrabajadorBecario(models.Model):
    trabajador = models.ForeignKey(Trabajador, on_delete=models.CASCADE)
    becario = models.ForeignKey(Becario, on_delete=models.CASCADE)
    fecha_ingreso = models.DateField(auto_now_add=True)
    recibo_nomina = models.FileField(upload_to='recibo_nomina/')
    ine = models.FileField(upload_to='ine/')

    def __str__(self):
        return "{} - {} - {}".format(self.trabajador, self.becario, self.anio)

# Clase para solicitud de beca
class Solicitud(models.Model):
    trabajador_becario = models.ForeignKey(TrabajadorBecario, on_delete=models.CASCADE)
    grado = models.ForeignKey(Grado, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=1)
    promedio = models.FloatField()
    boleta = models.FileField(upload_to='boleta/')
    obtuvo_beca = models.BooleanField(default=False, null=True, blank=True)
    usuario_responsable = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return "{} - {} - {} - {}".format(self.trabajador_becario, self.grado, self.tipo, self.promedio)

# Clase para solicitud especial de beca
class SolicitudEspecial(models.Model):
    trabajador_becario = models.ForeignKey(TrabajadorBecario, on_delete=models.CASCADE)
    diagnostico_medico = models.CharField(max_length=128)
    tipo_educacion = models.CharField(max_length=128)
    certificado_medico = models.FileField(upload_to='certificado_medico/')
    certificado_escolar = models.FileField(upload_to='certificado_escolar/')
    obtuvo_beca = models.BooleanField(default=False, null=True, blank=True)

    def __str__(self):
        return "{} - {} - {}".format(self.trabajador_becario, self.diagnostico_medico, self.tipo_educacion)
