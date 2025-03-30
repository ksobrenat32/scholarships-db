from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required
from becas_sntsa.forms import TrabajadorCreateForm, BecarioCreateForm, SolicitudNormalCreateForm, SolicitudEspecialCreateForm
from becas_sntsa.models import Trabajador, Becario, SolicitudNormal, SolicitudEspecial
from django.http import HttpResponseForbidden, FileResponse
from django.conf import settings
import os
import re

# Create your views here.

# Middleware to check if user has a linked trabajador
def trabajador_required(view_func):
    def _wrapped_view_func(request, *args, **kwargs):
        if request.user.is_authenticated:
            try:
                request.user.trabajador
            except Trabajador.DoesNotExist:
                return redirect('create_trabajador')
        return view_func(request, *args, **kwargs)
    return _wrapped_view_func

# Home view
def home(request):
    return render(request, 'home.html')

# Signup view
def signup(request):
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

# Signout view
def signout(request):
    logout(request)
    return redirect('home')

# Signin view
def signin(request):
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

# Becas view
@login_required
@trabajador_required
def becas(request):
    return render(request, 'becas.html')

# Create_Trabajador view
@login_required
def create_trabajador(request):
    if request.method == 'GET':
        return render(request, 'create_trabajador.html', {'form': TrabajadorCreateForm()})
    elif request.method == 'POST':
        try:
            form = TrabajadorCreateForm(request.POST, request.FILES)
            if form.is_valid():
                trabajador = form.save(commit=False)
                trabajador.usuario = User.objects.get(username = request.user.username)
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

# Create_Becario view
@login_required
@trabajador_required
def create_becario(request):
    if request.method == 'GET':
        return render(request, 'create_becario.html', {'form': BecarioCreateForm()})
    elif request.method == 'POST':
        try:
            form = BecarioCreateForm(request.POST, request.FILES)
            if form.is_valid():
                becario = form.save(commit=False)
                becario.trabajador = User.objects.get(username = request.user.username)
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

# Create_SolicitudNormal view
@login_required
@trabajador_required
def create_solicitud_normal(request):
    if request.method == 'GET':
        form = SolicitudNormalCreateForm(user=request.user)
        return render(request, 'create_solicitud_normal.html', {'form': form})
    elif request.method == 'POST':
        form = SolicitudNormalCreateForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            solicitud = form.save(commit=False)
            solicitud.becario = form.cleaned_data['becario']
            solicitud.estado = 'P'  # Set default estado to 'En progreso'
            solicitud.save()
            return redirect('becas')
        else:
            return render(request, 'create_solicitud_normal.html', {'form': form, 'error': 'Error en la solicitud'})

# Create_SolicitudEspecial view
@login_required
@trabajador_required
def create_solicitud_especial(request):
    if request.method == 'GET':
        form = SolicitudEspecialCreateForm(user=request.user)
        return render(request, 'create_solicitud_especial.html', {'form': form})
    elif request.method == 'POST':
        form = SolicitudEspecialCreateForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            solicitud = form.save(commit=False)
            solicitud.becario = form.cleaned_data['becario']
            solicitud.estado = 'P'  # Set default estado to 'En progreso'
            solicitud.save()
            return redirect('becas')
        else:
            return render(request, 'create_solicitud_especial.html', {'form': form, 'error': 'Error en la solicitud'})

# File download view
@login_required
def download_file(request, file_path):
    if not request.user.is_staff:
        return HttpResponseForbidden("You do not have permission to access this file.")

    file_full_path = os.path.join(settings.MEDIA_ROOT, file_path)
    if os.path.exists(file_full_path):
        return FileResponse(open(file_full_path, 'rb'))
    else:
        return HttpResponseForbidden("File not found.")

# View to see becarios
@login_required
@trabajador_required
def ver_becarios(request):
    becarios = Becario.objects.filter(trabajador=request.user)
    return render(request, 'ver_becarios.html', {'becarios': becarios})

# View to see solicitudes
@login_required
@trabajador_required
def ver_solicitudes(request):
    solicitudes_normales = SolicitudNormal.objects.filter(becario__trabajador=request.user)
    solicitudes_especiales = SolicitudEspecial.objects.filter(becario__trabajador=request.user)
    return render(request, 'ver_solicitudes.html', {
        'solicitudes_normales': solicitudes_normales,
        'solicitudes_especiales': solicitudes_especiales
    })

