from django.db import models
from django.contrib.auth.models import User

# Create your models here.

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

# Clase para el modelo de Trabajador
class Trabajador(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)

    nombre = models.CharField(max_length=128)
    apellido_paterno = models.CharField(max_length=128)
    apellido_materno = models.CharField(max_length=128, null=True, blank=True)
    curp_archivo = models.FileField(upload_to='curp/')

    telefono = models.CharField(max_length=16)
    correo = models.EmailField()

    seccion = models.ForeignKey(Seccion, on_delete=models.PROTECT)
    puesto = models.ForeignKey(Puesto, on_delete=models.PROTECT)
    lugar_adscripcion = models.ForeignKey(LugarAdscripcion, on_delete=models.PROTECT)

    def __str__(self):
        return "{}".format(self.usuario.username)

# Clase para el modelo de Becario, hereda de Usuario
class Becario(models.Model):
    trabajador = models.ForeignKey(User, on_delete=models.CASCADE)

    nombre = models.CharField(max_length=128)
    apellido_paterno = models.CharField(max_length=128)
    apellido_materno = models.CharField(max_length=128, null=True, blank=True)
    curp = models.CharField(max_length=18)
    curp_archivo = models.FileField(upload_to='curp/')

    acta_nacimiento = models.FileField(upload_to='acta_nacimiento/')

    def __str__(self):
        return "{}".format(self.curp)

    def get_sexo(self) -> str:
        return self.curp[10]

    def get_fecha_nacimiento(self) -> str:
        return "{}-{}-{}".format(self.curp[4:8], self.curp[8:10], self.curp[6:8])

# Clase para solicitud de beca
class Solicitud(models.Model):
    becario = models.ForeignKey(Becario, on_delete=models.CASCADE)
    fecha_solicitud = models.DateField(auto_now_add=True)
    recibo_nomina = models.FileField(upload_to='recibo_nomina/')
    ine = models.FileField(upload_to='ine/')

# Clase para solicitud normal de beca
class SolicitudNormal(Solicitud):
    grado = models.ForeignKey(Grado, on_delete=models.CASCADE)
    promedio = models.FloatField()
    boleta = models.FileField(upload_to='boleta/')
    obtuvo_beca = models.BooleanField(default=False, null=True, blank=True)

    def __str__(self):
        return "{} - {} - {}".format(self.becario, self.fecha_solicitud, self.obtuvo_beca)

# Clase para solicitud especial de beca
class SolicitudEspecial(Solicitud):
    diagnostico_medico = models.CharField(max_length=128)
    tipo_educacion = models.CharField(max_length=128)
    certificado_medico = models.FileField(upload_to='certificado_medico/')
    certificado_escolar = models.FileField(upload_to='certificado_escolar/')
    obtuvo_beca = models.BooleanField(default=False, null=True, blank=True)

    def __str__(self):
        return "{} - {} - {}".format(self.becario, self.fecha_solicitud, self.obtuvo_beca)
