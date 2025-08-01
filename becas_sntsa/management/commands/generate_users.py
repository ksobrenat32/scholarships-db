# Script to generate users for testing as json
from django.core.management.base import BaseCommand
import random
from faker import Faker
from becas_sntsa.models import User, Trabajador, Becario, Solicitud, Seccion, Puesto, Jurisdiccion, LugarAdscripcion, Grado, SolicitudAprovechamiento, SolicitudExcelencia, SolicitudEspecial

# Generate Mexican CURP
def generate_curp(nombre, apellido_paterno, apellido_materno):
    curp = ""
    # First letter of the last name
    curp += apellido_paterno[0].upper()
    # First vowel of the last name
    for letter in apellido_paterno[1:]:
        if letter.lower() in "aeiou":
            curp += letter.upper()
            break
    # First letter of the mother's last name
    curp += apellido_materno[0].upper()
    # First letter of the first name
    curp += nombre[0].upper()
    # Random two last digits of year of birth
    year = random.randint(0, 99)
    curp += str(year).zfill(2)
    # Month of birth
    month = random.randint(1, 12)
    curp += str(month).zfill(2)
    # Day of birth
    day = random.randint(1, 31)
    curp += str(day).zfill(2)
    # Random sex
    curp += random.choice(["H", "M"])
    # Random state
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    for _ in range(2):
        curp += random.choice(letters)
    # Random consonants
    consonants = "BCDFGHJKLMNPQRSTVWXYZ"
    for _ in range(3):
        curp += random.choice(consonants)
    # Two random digits
    for _ in range(2):
        curp += str(random.randint(0, 9))

    return curp

# Create the users with a trabajador
def create_trabajador() -> Trabajador:
    # Create a Faker instance
    fake = Faker('es_MX')

    nombre = fake.first_name()
    apellido_paterno = fake.last_name()
    apellido_materno = fake.last_name()
    telefono = random.randint(1000000000, 9999999999)
    correo = fake.email()
    curp = generate_curp(nombre, apellido_paterno, apellido_materno)

    # Get all the sections
    secciones = Seccion.objects.all()
    seccion = random.choice(secciones)

    # Get all the positions
    puestos = Puesto.objects.all()
    puesto = random.choice(puestos)

    # Get all the places
    lugares = LugarAdscripcion.objects.all()
    lugar_adscripcion = random.choice(lugares)

    # Get all jurisdictions
    jurisdicciones = Jurisdiccion.objects.all()
    jurisdiccion = random.choice(jurisdicciones)

    # Approved status
    aprobado = random.choice([True, False])

    # Create the user
    user = User.objects.create_user(
        username=curp,
        password=curp
    )
    user.save()

    # Create the trabajador
    trabajador = Trabajador(
        usuario=user,
        nombre=nombre,
        apellido_paterno=apellido_paterno,
        apellido_materno=apellido_materno,
        telefono=telefono,
        correo=correo,
        seccion=seccion,
        puesto=puesto,
        jurisdiccion=jurisdiccion,
        lugar_adscripcion=lugar_adscripcion,
        aprobado=aprobado
    )

    trabajador.save()
    return trabajador

def create_becario(trabajador: Trabajador) -> Becario:
    # Create a Faker instance
    fake = Faker('es_MX')

    nombre = fake.first_name()
    apellido_paterno = fake.last_name()
    apellido_materno = fake.last_name()
    curp = generate_curp(nombre, apellido_paterno, apellido_materno)

    # Create the becario
    becario = Becario(
        trabajador=trabajador.usuario,
        nombre=nombre,
        apellido_paterno=apellido_paterno,
        apellido_materno=apellido_materno,
        curp=curp
    )

    becario.save()
    return becario

def create_solicitud(becario: Becario) -> Solicitud:
    # Create a Faker instance
    fake = Faker('es_MX')

    # Create the solicitud
    fecha_solicitud=fake.date()
    estado = random.choice(Solicitud._meta.get_field('estado').choices)[0]

    # If estado is 'P', check if the becario has any pending solicitud
    if estado == "P":
        if Solicitud.objects.filter(becario=becario, estado='P').exists():
            estado = "F"  # Change to "Beca no otorgada" if already exists

    # If the estado is 'E' (Especial), add notes
    if estado == "E":
        notas = fake.text(max_nb_chars=200)
    else:
        notas = ""

    type = random.choice([SolicitudAprovechamiento, SolicitudExcelencia, SolicitudEspecial])

    # Solicitud Aprovechamiento, Excelencia or Especial
    if type == SolicitudAprovechamiento:
        grado = random.choice(Grado.objects.all())
        promedio = float(random.randint(70, 100)) / 10

        solicitud = SolicitudAprovechamiento(
            becario=becario,
            fecha_solicitud=fecha_solicitud,
            estado=estado,
            notas=notas,
            grado=grado,
            promedio=promedio,
        )
    elif type == SolicitudExcelencia:
        grado = random.choice(Grado.objects.all())
        promedio = float(random.randint(70, 100)) / 10
        carrera = fake.text(max_nb_chars=128)

        solicitud = SolicitudExcelencia(
            becario=becario,
            fecha_solicitud=fecha_solicitud,
            estado=estado,
            notas=notas,
            grado=grado,
            promedio=promedio,
            carrera=carrera,
        )
    else:
        # Especial
        diagnostico_medico = fake.text(max_nb_chars=128)
        tipo_educacion = fake.text(max_nb_chars=128)

        solicitud = SolicitudEspecial(
            becario=becario,
            fecha_solicitud=fecha_solicitud,
            estado=estado,
            notas=notas,
            diagnostico_medico=diagnostico_medico,
            tipo_educacion=tipo_educacion
        )

    solicitud.save()
    return solicitud

class Command(BaseCommand):
    help = 'Generate users for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--num_users',
            type=int,
            default=10,
            help='Number of users (trabajadores) to create'
        )
        parser.add_argument(
            '--min-becarios',
            type=int,
            default=1,
            help='Minimum number of becarios per trabajador (default: 1)'
        )
        parser.add_argument(
            '--max-becarios',
            type=int,
            default=5,
            help='Maximum number of becarios per trabajador (default: 5)'
        )
        parser.add_argument(
            '--min-solicitudes',
            type=int,
            default=1,
            help='Minimum number of solicitudes per becario (default: 1)'
        )
        parser.add_argument(
            '--max-solicitudes',
            type=int,
            default=5,
            help='Maximum number of solicitudes per becario (default: 5)'
        )

    def handle(self, *args, **options):
        num_users = options['num_users']
        min_becarios = options['min_becarios']
        max_becarios = options['max_becarios']
        min_solicitudes = options['min_solicitudes']
        max_solicitudes = options['max_solicitudes']

        self.stdout.write(
            self.style.SUCCESS(
                f'Creating {num_users} users with {min_becarios}-{max_becarios} becarios each '
                f'and {min_solicitudes}-{max_solicitudes} solicitudes per becario...'
            )
        )

        for i in range(num_users):
            trabajador = create_trabajador()
            # Create from min_becarios to max_becarios Becarios for each Trabajador
            num_becarios = random.randint(min_becarios, max_becarios)
            for _ in range(num_becarios):
                becario = create_becario(trabajador)
                # Create from min_solicitudes to max_solicitudes Solicitudes for each Becario
                num_solicitudes = random.randint(min_solicitudes, max_solicitudes)
                for _ in range(num_solicitudes):
                    create_solicitud(becario)
            
            if (i + 1) % 5 == 0:
                self.stdout.write(f'Created {i + 1}/{num_users} users...')

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {num_users} users with their becarios and solicitudes!')
        )
