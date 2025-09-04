"""
Views for the becas_sntsa app.

This file contains the view functions that handle requests and responses for the scholarship application system.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required
from becas_sntsa.forms import TrabajadorCreateForm, BecarioCreateForm, SolicitudAprovechamientoCreateForm, SolicitudExcelenciaCreateForm, SolicitudEspecialCreateForm, TrabajadorEditForm, BecarioEditForm
from becas_sntsa.models import Trabajador, Becario, Solicitud, SolicitudAprovechamiento, SolicitudExcelencia, SolicitudEspecial
from django.http import HttpResponseForbidden, FileResponse
from django.conf import settings
import os
import re


def trabajador_required(view_func):
    """
    Decorator to ensure that the user has a linked 'Trabajador' profile.

    If the user is authenticated but does not have a 'Trabajador' profile,
    they are redirected to the 'create_trabajador' page.

    Args:
        view_func (function): The view function to be decorated.

    Returns:
        function: The wrapped view function.
    """
    def _wrapped_view_func(request, *args, **kwargs):
        if request.user.is_authenticated:
            try:
                request.user.trabajador
            except Trabajador.DoesNotExist:
                return redirect('create_trabajador')
        return view_func(request, *args, **kwargs)
    return _wrapped_view_func


def approved_required(view_func):
    """
    Decorator to ensure that the user's 'Trabajador' profile has been approved.

    If the user's profile is not approved, they are shown a page indicating
    that they are waiting for verification.

    Args:
        view_func (function): The view function to be decorated.

    Returns:
        function: The wrapped view function.
    """
    def _wrapped_view_func(request, *args, **kwargs):
        if request.user.is_authenticated:
            try:
                trabajador = request.user.trabajador
                if not trabajador.aprobado:
                    return render(request, 'espera_verificacion.html', {'user': request.user})
            except Trabajador.DoesNotExist:
                return redirect('create_trabajador')
        return view_func(request, *args, **kwargs)
    return _wrapped_view_func


def home(request):
    """
    Renders the home page.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: The rendered home page.
    """
    return render(request, 'home.html')


def signup(request):
    """
    Handles user registration.

    On GET, it displays the registration form.
    On POST, it validates the form and creates a new user.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: The rendered registration page or a redirect to the
                      'create_trabajador' page.
    """
    if request.method == 'GET':
        return render(request, 'signup.html', {'form': UserCreationForm()})
    elif request.method == 'POST':
        curp = request.POST['username']
        curp_regex = re.compile(r'^([A-Z]{4}\d{6}[HM][A-Z]{5}[A-Z0-9]{2})$')
        if not curp_regex.match(curp):
            return render(request, 'signup.html', {
                'form': UserCreationForm(),
                'error': 'Formato de CURP inválido'
            })
        if request.POST['password1'] == request.POST['password2']:
            try:
                user = User.objects.create_user(
                    request.POST['username'], password=request.POST['password1'])
                user.save()
                login(request, user)
                return redirect('create_trabajador')
            except IntegrityError:
                return render(request, 'signup.html', {
                    'form': UserCreationForm(),
                    'error': 'El usuario ya existe'
                })
            # Ignore if the error is related to password complexity
            except Exception as e:
                print('Exception: ', e)
                return render(request, 'signup.html', {
                    'form': UserCreationForm(),
                    'error': 'Error al crear el usuario'
                })
        else:
            return render(request, 'signup.html', {
                'form': UserCreationForm(),
                'error': 'Las contraseñas no coinciden'
            })


def signout(request):
    """
    Logs the user out and redirects to the home page.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponseRedirect: A redirect to the home page.
    """
    logout(request)
    return redirect('home')


def signin(request):
    """
    Handles user login.

    On GET, it displays the login form.
    On POST, it authenticates the user and logs them in.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: The rendered login page or a redirect to the 'becas' page.
    """
    if request.method == 'GET':
        return render(request, 'signin.html', {'form': AuthenticationForm()})
    elif request.method == 'POST':
        user = authenticate(request, username=request.POST['username'],
                            password=request.POST['password'])
        if user is None:
            return render(request, 'signin.html', {
                'form': AuthenticationForm(),
                'error': 'Usuario o contraseña inválidos'
            })
        else:
            login(request, user)
            return redirect('becas')


@login_required
@trabajador_required
def becas(request):
    """
    Renders the main scholarship page.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: The rendered scholarship page.
    """
    return render(request, 'becas.html')


@login_required
def create_trabajador(request):
    """
    Handles the creation of a 'Trabajador' profile.

    On GET, it displays the form to create a profile.
    On POST, it validates the form and creates the profile.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: The rendered form page or a redirect to the 'becas' page.
    """
    if request.method == 'GET':
        return render(request, 'create_trabajador.html', {'form': TrabajadorCreateForm()})
    elif request.method == 'POST':
        try:
            form = TrabajadorCreateForm(request.POST, request.FILES)
            if form.is_valid():
                trabajador = form.save(commit=False)
                trabajador.usuario = User.objects.get(
                    username=request.user.username)
                trabajador.save()
                return redirect('becas')
            else:
                print('Form errors: ', form.errors)
                return render(request, 'create_trabajador.html', {'form': form})
        except ValueError:
            return render(request, 'create_trabajador.html', {
                'form': TrabajadorCreateForm(),
                'error': 'Existe un error en los datos ingresados'
            })
        except IntegrityError:
            return render(request, 'create_trabajador.html', {
                'form': TrabajadorCreateForm(),
                'error': 'El trabajador ya existe'
            })
        except Exception as e:
            print('Exception: ', e)
            return render(request, 'create_trabajador.html', {
                'form': TrabajadorCreateForm(),
                'error': 'Error al crear el trabajador'
            })


@login_required
@trabajador_required
@approved_required
def create_becario(request):
    """
    Handles the creation of a 'Becario' (scholar) profile.

    On GET, it displays the form to create a profile.
    On POST, it validates the form and creates the profile.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: The rendered form page or a redirect to the home page.
    """
    if request.method == 'GET':
        return render(request, 'create_becario.html', {'form': BecarioCreateForm()})
    elif request.method == 'POST':
        try:
            form = BecarioCreateForm(request.POST, request.FILES)
            if form.is_valid():
                becario = form.save(commit=False)
                becario.trabajador = User.objects.get(
                    username=request.user.username)
                becario.save()
                return redirect('home')
            else:
                print('Form errors: ', form.errors)
                return render(request, 'create_becario.html', {'form': form})
        except ValueError:
            return render(request, 'create_becario.html', {
                'form': BecarioCreateForm(),
                'error': 'Existe un error en los datos ingresados'
            })
        except IntegrityError:
            return render(request, 'create_becario.html', {
                'form': BecarioCreateForm(),
                'error': 'El becario ya existe'
            })
        except Exception as e:
            print('Exception: ', e)
            return render(request, 'create_becario.html', {
                'form': BecarioCreateForm(),
                'error': 'Error al crear el becario'
            })


@login_required
@trabajador_required
@approved_required
def create_solicitud_aprovechamiento(request):
    """
    Handles the creation of a scholarship application for academic achievement.

    On GET, it displays the application form.
    On POST, it validates the form and creates the application.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: The rendered form page or a redirect to the 'becas' page.
    """
    if request.method == 'GET':
        form = SolicitudAprovechamientoCreateForm(user=request.user)
        return render(request, 'create_solicitud_aprovechamiento.html', {'form': form})
    elif request.method == 'POST':
        form = SolicitudAprovechamientoCreateForm(
            request.POST, request.FILES, user=request.user)
        if form.is_valid():
            solicitud = form.save(commit=False)
            solicitud.becario = form.cleaned_data['becario']
            solicitud.estado = 'R'  # Set default estado to 'Recibida'

            # Check if the becario has any other pending solicitud in estado 'R' or 'P'
            if SolicitudAprovechamiento.objects.filter(becario=solicitud.becario, estado__in=['R', 'P']).exists():
                return render(request, 'create_solicitud_aprovechamiento.html', {
                    'form': form,
                    'error': 'El becario ya tiene una solicitud pendiente en esta categoría.'
                })

            solicitud.save()
            return redirect('becas')
        else:
            return render(request, 'create_solicitud_aprovechamiento.html', {'form': form, 'error': 'Error en la solicitud'})


@login_required
@trabajador_required
@approved_required
def create_solicitud_excelencia(request):
    """
    Handles the creation of a scholarship application for academic excellence.

    On GET, it displays the application form.
    On POST, it validates the form and creates the application.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: The rendered form page or a redirect to the 'becas' page.
    """
    if request.method == 'GET':
        form = SolicitudExcelenciaCreateForm(user=request.user)
        return render(request, 'create_solicitud_excelencia.html', {'form': form})
    elif request.method == 'POST':
        form = SolicitudExcelenciaCreateForm(
            request.POST, request.FILES, user=request.user)
        if form.is_valid():
            solicitud = form.save(commit=False)
            solicitud.becario = form.cleaned_data['becario']
            solicitud.estado = 'R'  # Set default estado to 'Recibida'

            # Check if the becario has any other pending solicitud in estado 'R' or 'P'
            if SolicitudExcelencia.objects.filter(becario=solicitud.becario, estado__in=['R', 'P']).exists():
                return render(request, 'create_solicitud_excelencia.html', {
                    'form': form,
                    'error': 'El becario ya tiene una solicitud pendiente en esta categoría.'
                })

            solicitud.save()
            return redirect('becas')
        else:
            return render(request, 'create_solicitud_excelencia.html', {'form': form, 'error': 'Error en la solicitud'})


@login_required
@trabajador_required
@approved_required
def create_solicitud_especial(request):
    """
    Handles the creation of a special scholarship application.

    On GET, it displays the application form.
    On POST, it validates the form and creates the application.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: The rendered form page or a redirect to the 'becas' page.
    """
    if request.method == 'GET':
        form = SolicitudEspecialCreateForm(user=request.user)
        return render(request, 'create_solicitud_especial.html', {'form': form})
    elif request.method == 'POST':
        form = SolicitudEspecialCreateForm(
            request.POST, request.FILES, user=request.user)
        if form.is_valid():
            solicitud = form.save(commit=False)
            solicitud.becario = form.cleaned_data['becario']
            solicitud.estado = 'R'  # Set default estado to 'Recibida'

            # Check if the becario has any other pending solicitud in estado 'R' or 'P'
            if SolicitudEspecial.objects.filter(becario=solicitud.becario, estado__in=['R', 'P']).exists():
                return render(request, 'create_solicitud_especial.html', {
                    'form': form,
                    'error': 'El becario ya tiene una solicitud pendiente en esta categoría.'
                })

            solicitud.save()
            return redirect('becas')
        else:
            return render(request, 'create_solicitud_especial.html', {'form': form, 'error': 'Error en la solicitud'})


@login_required
def download_file(request, file_path):
    """
    Handles file downloads, ensuring that only staff users can access them.

    Args:
        request (HttpRequest): The request object.
        file_path (str): The path to the file to be downloaded.

    Returns:
        FileResponse or HttpResponseForbidden: The file to be downloaded or a
                                               forbidden response.
    """
    if not request.user.is_staff:
        return HttpResponseForbidden("You do not have permission to access this file.")

    normalized_path = os.path.normpath(file_path)
    file_full_path = os.path.join(settings.MEDIA_ROOT, normalized_path)

    # Resolve the real path to prevent directory traversal
    real_path = os.path.realpath(file_full_path)

    if not real_path.startswith(os.path.realpath(settings.MEDIA_ROOT)):
        return HttpResponseForbidden("Invalid file path.")

    if os.path.exists(real_path):
        return FileResponse(open(real_path, 'rb'))
    else:
        return HttpResponseForbidden("File not found.")


@login_required
@trabajador_required
@approved_required
def ver_becarios(request):
    """
    Displays a list of scholars associated with the current user.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: The rendered page with the list of scholars.
    """
    becarios = Becario.objects.filter(trabajador=request.user)
    return render(request, 'ver_becarios.html', {'becarios': becarios})


@login_required
@trabajador_required
@approved_required
def ver_solicitudes(request):
    """
    Displays a list of scholarship applications associated with the current user.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: The rendered page with the list of applications.
    """
    solicitudes_normales = SolicitudAprovechamiento.objects.filter(
        becario__trabajador=request.user)
    solicitudes_excelencia = SolicitudExcelencia.objects.filter(
        becario__trabajador=request.user)
    solicitudes_especiales = SolicitudEspecial.objects.filter(
        becario__trabajador=request.user)
    return render(request, 'ver_solicitudes.html', {
        'solicitudes_aprovechamiento': solicitudes_normales,
        'solicitudes_excelencia': solicitudes_excelencia,
        'solicitudes_especiales': solicitudes_especiales
    })


@login_required
@trabajador_required
def editar_usuario(request):
    """
    Handles the editing of a user's 'Trabajador' profile.

    On GET, it displays the form to edit the profile.
    On POST, it validates the form and updates the profile.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: The rendered form page or a redirect to the 'becas' page.
    """
    trabajador = request.user.trabajador
    if request.method == 'GET':
        form = TrabajadorEditForm(instance=trabajador)
        return render(request, 'editar_usuario.html', {'form': form})
    elif request.method == 'POST':
        form = TrabajadorEditForm(
            request.POST, request.FILES, instance=trabajador)
        if form.is_valid():
            form.save()
            return redirect('becas')
        else:
            return render(request, 'editar_usuario.html', {'form': form})


@login_required
@trabajador_required
@approved_required
def editar_becario(request, becario_id):
    """
    Handles the editing of a 'Becario' (scholar) profile.

    On GET, it displays the form to edit the profile.
    On POST, it validates the form and updates the profile.

    Args:
        request (HttpRequest): The request object.
        becario_id (int): The ID of the scholar to be edited.

    Returns:
        HttpResponse: The rendered form page or a redirect to the 'ver_becarios' page.
    """
    becario = get_object_or_404(Becario, id=becario_id, trabajador=request.user)

    # Check for valid solicitudes
    valid_solicitudes = Solicitud.objects.filter(
        becario=becario, estado__in=['R', 'P', 'T']).exists()
    if valid_solicitudes:
        return render(request, 'editar_becario.html', {
            'error': 'Este becario tiene una solicitud en curso o aprobada. No se puede editar. Por favor, crea un nuevo becario si es necesario.'
        })

    if request.method == 'GET':
        form = BecarioEditForm(instance=becario)
        return render(request, 'editar_becario.html', {'form': form, 'becario': becario})
    elif request.method == 'POST':
        form = BecarioEditForm(request.POST, request.FILES, instance=becario)
        if form.is_valid():
            form.save()
            return redirect('ver_becarios')
        else:
            return render(request, 'editar_becario.html', {'form': form, 'becario': becario})
