from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required
from main.forms import TrabajadorCreateForm, BecarioCreateForm
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

