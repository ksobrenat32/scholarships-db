"""
Models for the becas_sntsa app.

This file defines the database models for the scholarship application system.
It includes models for workers, scholars, applications, and related data.
"""
from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.


class Seccion(models.Model):
    """
    Represents a worker's section.

    Attributes:
        numero (int): The section number.
    """
    numero = models.IntegerField()

    def __str__(self):
        """
        Returns a string representation of the section.

        Returns:
            str: The section number as a string.
        """
        return str(self.numero)


class Puesto(models.Model):
    """
    Represents a worker's position.

    Attributes:
        clave (str): The position's key or code.
    """
    clave = models.CharField(max_length=8)

    def __str__(self):
        """
        Returns a string representation of the position.

        Returns:
            str: The position's key.
        """
        return self.clave


class Jurisdiccion(models.Model):
    """
    Represents a worker's jurisdiction.

    Attributes:
        clave (str): The jurisdiction's key or code.
    """
    clave = models.CharField(max_length=4)

    def __str__(self):
        """
        Returns a string representation of the jurisdiction.

        Returns:
            str: The jurisdiction's key.
        """
        return self.clave


class LugarAdscripcion(models.Model):
    """
    Represents a worker's place of assignment.

    Attributes:
        alias (str, optional): An alias for the place of assignment.
        nombre (str): The name of the place of assignment.
    """
    alias = models.CharField(max_length=32, null=True, blank=True)
    nombre = models.CharField(max_length=128)

    def __str__(self):
        """
        Returns a string representation of the place of assignment.

        Returns:
            str: The name of the place of assignment.
        """
        return self.nombre


class Grado(models.Model):
    """
    Represents a scholar's grade level.

    Attributes:
        clave (str): The grade's key or code.
        nombre (str): The name of the grade.
    """
    clave = models.CharField(max_length=4)
    nombre = models.CharField(max_length=64)

    def __str__(self):
        """
        Returns a string representation of the grade.

        Returns:
            str: The grade's key and name.
        """
        return "{} - {}".format(self.clave, self.nombre)


class Trabajador(models.Model):
    """
    Represents a worker who can apply for scholarships for their children.

    Attributes:
        usuario (User): A one-to-one relationship with the User model.
        nombre (str): The worker's first name.
        apellido_paterno (str): The worker's paternal last name.
        apellido_materno (str, optional): The worker's maternal last name.
        curp_archivo (FileField): The worker's CURP document.
        telefono (str): The worker's phone number.
        correo (EmailField): The worker's email address.
        seccion (Seccion): The worker's section.
        puesto (Puesto): The worker's position.
        jurisdiccion (Jurisdiccion): The worker's jurisdiction.
        lugar_adscripcion (LugarAdscripcion): The worker's place of assignment.
        aprobado (bool): A flag to indicate if the worker has been approved by an admin.
    """
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
    lugar_adscripcion = models.ForeignKey(
        LugarAdscripcion, on_delete=models.PROTECT)

    # Campo para verificar si el trabajador ha sido aprobado por el administrador
    aprobado = models.BooleanField(default=False)

    def __str__(self):
        """
        Returns a string representation of the worker.

        Returns:
            str: The worker's username.
        """
        return "{}".format(self.usuario.username)


class Becario(models.Model):
    """
    Represents a scholar (a worker's child) who is the beneficiary of a scholarship.

    Attributes:
        trabajador (User): The worker associated with the scholar.
        nombre (str): The scholar's first name.
        apellido_paterno (str): The scholar's paternal last name.
        apellido_materno (str, optional): The scholar's maternal last name.
        curp (str): The scholar's CURP.
        curp_archivo (FileField): The scholar's CURP document.
        acta_nacimiento (FileField): The scholar's birth certificate.
    """
    trabajador = models.ForeignKey(User, on_delete=models.CASCADE)

    nombre = models.CharField(max_length=128)
    apellido_paterno = models.CharField(max_length=128)
    apellido_materno = models.CharField(max_length=128, null=True, blank=True)
    curp = models.CharField(max_length=18)
    curp_archivo = models.FileField(upload_to='curp/')

    acta_nacimiento = models.FileField(upload_to='acta_nacimiento/')

    def __str__(self):
        """
        Returns a string representation of the scholar.

        Returns:
            str: The scholar's CURP.
        """
        return "{}".format(self.curp)

    def get_sexo(self) -> str:
        """
        Extracts the sex of the scholar from their CURP.

        Returns:
            str: The sex of the scholar ('H' for male, 'M' for female).
        """
        return self.curp[10]

    def get_fecha_nacimiento(self) -> str:
        """
        Extracts the birth date of the scholar from their CURP.

        Returns:
            str: The scholar's birth date in 'YYYY-MM-DD' format.
        """
        year = self.curp[4:6]
        month = self.curp[6:8]
        day = self.curp[8:10]

        # This is a simplification. It assumes that years > '23' belong to the 20th century.
        if int(year) > 23:
            full_year = "19" + year
        else:
            full_year = "20" + year

        return "{}-{}-{}".format(full_year, month, day)


class Solicitud(models.Model):
    """
    Represents a scholarship application.

    This is a base class for different types of scholarship applications.

    Attributes:
        becario (Becario): The scholar for whom the application is made.
        fecha_solicitud (DateField): The date the application was submitted.
        recibo_nomina (FileField): The worker's payroll receipt.
        ine (FileField): The worker's INE document.
        estado (str): The status of the application.
        notas (TextField, optional): Notes about the application.
    """
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
    estado = models.CharField(
        max_length=1, choices=ESTADO_CHOICES, default='P')
    notas = models.TextField(null=True, blank=True)

    class Meta:
        """
        Meta options for the Solicitud model.
        """
        constraints = [
            models.UniqueConstraint(
                fields=['becario'],
                condition=Q(estado='P'),
                name='unique_solicitud_en_espera'
            )
        ]


class SolicitudAprovechamiento(Solicitud):
    """
    Represents a scholarship application for academic achievement.

    Attributes:
        grado (Grado): The scholar's grade level.
        promedio (FloatField): The scholar's average grade.
        boleta (FileField): The scholar's report card.
    """
    grado = models.ForeignKey(Grado, on_delete=models.CASCADE)
    # From 6 to 10
    promedio = models.FloatField()
    boleta = models.FileField(upload_to='boleta/')

    def __str__(self):
        """
        Returns a string representation of the application.

        Returns:
            str: A summary of the application.
        """
        return "{} - {} - {}".format(self.becario, self.fecha_solicitud, self.estado)


class SolicitudExcelencia(Solicitud):
    """
    Represents a scholarship application for academic excellence.

    Attributes:
        grado (Grado): The scholar's grade level.
        promedio (FloatField): The scholar's average grade.
        boleta (FileField): The scholar's report card.
        carrera (str): The scholar's field of study.
    """
    grado = models.ForeignKey(Grado, on_delete=models.CASCADE)
    # From 6 to 10
    promedio = models.FloatField()
    boleta = models.FileField(upload_to='boleta/')
    carrera = models.CharField(max_length=128)

    def __str__(self):
        """
        Returns a string representation of the application.

        Returns:
            str: A summary of the application.
        """
        return "{} - {} - {}".format(self.becario, self.fecha_solicitud, self.estado)


class SolicitudEspecial(Solicitud):
    """
    Represents a special scholarship application.

    Attributes:
        diagnostico_medico (str): The medical diagnosis for the special case.
        tipo_educacion (str): The type of education for the special case.
        certificado_medico (FileField): The medical certificate.
        certificado_escolar (FileField): The school certificate.
    """
    diagnostico_medico = models.CharField(max_length=128)
    tipo_educacion = models.CharField(max_length=128)
    certificado_medico = models.FileField(upload_to='certificado_medico/')
    certificado_escolar = models.FileField(
        upload_to='certificado_escolar/')

    def __str__(self):
        """
        Returns a string representation of the application.

        Returns:
            str: A summary of the application.
        """
        return "{} - {} - {}".format(self.becario, self.fecha_solicitud, self.estado)
