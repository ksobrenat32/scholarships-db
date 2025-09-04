from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.utils import timezone

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

# Clase para la jurisdiccion de los trabajadores
class Jurisdiccion(models.Model):
    clave = models.CharField(max_length=4)

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

    telefono = models.CharField(max_length=10)
    correo = models.EmailField()

    seccion = models.ForeignKey(Seccion, on_delete=models.PROTECT)
    puesto = models.ForeignKey(Puesto, on_delete=models.PROTECT)
    jurisdiccion = models.ForeignKey(Jurisdiccion, on_delete=models.PROTECT)
    lugar_adscripcion = models.ForeignKey(LugarAdscripcion, on_delete=models.PROTECT)

    # Campo para verificar si el trabajador ha sido aprobado por el administrador
    aprobado = models.BooleanField(default=False)

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
        year = self.curp[4:6]
        month = self.curp[6:8]
        day = self.curp[8:10]

        # This is a simplification. It assumes that years > '23' belong to the 20th century.
        if int(year) > 23:
            full_year = "19" + year
        else:
            full_year = "20" + year

        return "{}-{}-{}".format(full_year, month, day)

# Clase para solicitud de beca
class Solicitud(models.Model):
    becario = models.ForeignKey(Becario, on_delete=models.CASCADE)
    # Added automatically
    fecha_solicitud = models.DateField(default=timezone.now)
    # Of the Trabajador
    recibo_nomina = models.FileField(upload_to='recibo_nomina/')
    # Of the Trabajador
    ine = models.FileField(upload_to='ine/')
    ESTADO_CHOICES = [
        ('R', 'Solicitud recibida'),
        ('E', 'Error en documentos, revisar notas'),
        ('P', 'En espera de resultados'),
        ('T', 'Beca otorgada'),
        ('F', 'Beca no otorgada'),
    ]
    estado = models.CharField(max_length=1, choices=ESTADO_CHOICES, default='P')
    notas = models.TextField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['becario'],
                condition=Q(estado='P'),
                name='unique_solicitud_en_espera'
            )
        ]

# Clase para solicitud de Aprovechamiento
class SolicitudAprovechamiento(Solicitud):
    grado = models.ForeignKey(Grado, on_delete=models.CASCADE)
    # From 6 to 10
    promedio = models.FloatField()
    boleta = models.FileField(upload_to='boleta/')

    def __str__(self):
        return "{} - {} - {}".format(self.becario, self.fecha_solicitud, self.estado)


# Clase para solicitud de excelencia
class SolicitudExcelencia(Solicitud):
    grado = models.ForeignKey(Grado, on_delete=models.CASCADE)
    # From 6 to 10
    promedio = models.FloatField()
    boleta = models.FileField(upload_to='boleta/')
    carrera = models.CharField(max_length=128)

    def __str__(self):
        return "{} - {} - {}".format(self.becario, self.fecha_solicitud, self.estado)

# Clase para solicitud especial de beca
class SolicitudEspecial(Solicitud):
    diagnostico_medico = models.CharField(max_length=128)
    tipo_educacion = models.CharField(max_length=128)
    certificado_medico = models.FileField(upload_to='certificado_medico/')
    certificado_escolar = models.FileField(upload_to='certificado_escolar/')

    def __str__(self):
        return "{} - {} - {}".format(self.becario, self.fecha_solicitud, self.estado)
