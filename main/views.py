from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required
from main.forms import UsuarioCreateForm, TrabajadorCreateForm, BecarioCreateForm
from main.models import Usuario
from django.http import HttpResponseForbidden, FileResponse
from django.conf import settings
import os

# Create your views here.

# Home view


def home(request):
    return render(request, 'home.html')

# Signup view


def signup(request):
    if request.method == 'GET':
        return render(request, 'signup.html', {'form': UserCreationForm()})
    elif request.method == 'POST':
        if request.POST['password1'] == request.POST['password2']:
            try:
                user = User.objects.create_user(
                    request.POST['username'], password=request.POST['password1'])
                user.save()
                login(request, user)
                return redirect('becas')
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
def becas(request):
    return render(request, 'becas.html')

# Create_Usuario view

@login_required
def create_usuario(request):
    if request.method == 'GET':
        return render(request, 'create_usuario.html', {'form': UsuarioCreateForm()})
    elif request.method == 'POST':
        try:
            form = UsuarioCreateForm(request.POST, request.FILES)
            if form.is_valid():
                usuario = form.save()
                curp = usuario.curp
                # Redirect with the curp of the user created
                if(usuario.es_trabajador):
                    return redirect('create_trabajador', curp=curp)
                if(usuario.es_becario):
                    return redirect('create_becario', curp=curp)
            else:
                return render(request, 'create_usuario.html', {'form': form})
        except ValueError:
            return render(request, 'create_usuario.html', {
                'form': UsuarioCreateForm(),
                'error': 'Existe un error en los datos ingresados'
            })
        except IntegrityError:
            return render(request, 'create_usuario.html', {
                'form': UsuarioCreateForm(),
                'error': 'El usuario ya existe'
            })
        except Exception as e:
            print('Exception: ', e)
            return render(request, 'create_usuario.html', {
                'form': UsuarioCreateForm(),
                'error': 'Error al crear el usuario'
            })

# Create_Trabajador view

@login_required
def create_trabajador(request, curp):
    if request.method == 'GET':
        return render(request, 'create_trabajador.html', {'form': TrabajadorCreateForm(), 'curp': curp})
    elif request.method == 'POST':
        try:
            form = TrabajadorCreateForm(request.POST)
            if form.is_valid():
                trabajador = form.save(commit=False)
                trabajador.usuario = Usuario.objects.get(curp=curp)
                trabajador.save()
                if trabajador.usuario.es_becario:
                    return redirect('create_becario', curp=curp)
                return redirect('home')
            else:
                return render(request, 'create_trabajador.html', {'form': form, 'curp': curp})
        except ValueError:
            return render(request, 'create_trabajador.html', {
                'form': TrabajadorCreateForm(),
                'curp': curp,
                'error': 'Existe un error en los datos ingresados'
            })
        except IntegrityError:
            return render(request, 'create_trabajador.html', {
                'form': TrabajadorCreateForm(),
                'curp': curp,
                'error': 'El trabajador ya existe'
            })
        except Exception as e:
            print('Exception: ', e)
            return render(request, 'create_trabajador.html', {
                'form': TrabajadorCreateForm(),
                'curp': curp,
                'error': 'Error al crear el trabajador'
            })

# Create_Becario view

@login_required
def create_becario(request, curp):
    if request.method == 'GET':
        return render(request, 'create_becario.html', {'form': BecarioCreateForm(), 'curp': curp})
    elif request.method == 'POST':
        try:
            form = BecarioCreateForm(request.POST, request.FILES)
            if form.is_valid():
                becario = form.save(commit=False)
                becario.usuario = Usuario.objects.get(curp=curp)
                becario.save()
                return redirect('home')
            else:
                return render(request, 'create_becario.html', {'form': form, 'curp': curp})
        except ValueError:
            return render(request, 'create_becario.html', {
                'form': BecarioCreateForm(),
                'curp': curp,
                'error': 'Existe un error en los datos ingresados'
            })
        except IntegrityError:
            return render(request, 'create_becario.html', {
                'form': BecarioCreateForm(),
                'curp': curp,
                'error': 'El becario ya existe'
            })
        except Exception as e:
            print('Exception: ', e)
            return render(request, 'create_becario.html', {
                'form': BecarioCreateForm(),
                'curp': curp,
                'error': 'Error al crear el becario'
            })

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

