from django import forms
from usuarios.models import DatosPersonales
from login_app.models import Usuario, Rol
from django.contrib.auth.hashers import make_password

class UsuarioForm(forms.Form):
    nombres = forms.CharField(max_length=100)
    apellido_paterno = forms.CharField(max_length=100)
    apellido_materno = forms.CharField(max_length=100, required=False)
    correo = forms.EmailField()
    numero_empleado = forms.CharField(max_length=50)
    telefono = forms.CharField(max_length=20, required=False)

    rol = forms.ModelChoiceField(queryset=Rol.objects.all())
    contraseña = forms.CharField(widget=forms.PasswordInput())
