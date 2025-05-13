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

class VerUsuarioForm(forms.Form):
    nombres = forms.CharField(label='Nombres')
    apellido_paterno = forms.CharField(label='Apellido Paterno')
    apellido_materno = forms.CharField(label='Apellido Materno', required=False)
    correo = forms.EmailField(label='Correo institucional')
    numero_empleado = forms.CharField(label='Número de empleado')
    telefono = forms.CharField(label='Teléfono')

    id_rol = forms.ModelChoiceField(
        queryset=Rol.objects.all(),
        label='Rol',
        required=False
    )
    estado = forms.BooleanField(label='Usuario activo', required=False)

    nueva_contraseña = forms.CharField(
        label='Nueva contraseña',
        widget=forms.PasswordInput,
        required=False
    )
    confirmar_contraseña = forms.CharField(
        label='Confirmar nueva contraseña',
        widget=forms.PasswordInput,
        required=False
    )

    def __init__(self, *args, **kwargs):
        self.is_guest = kwargs.pop('is_guest', False)
        super(VerUsuarioForm, self).__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

            if self.is_guest:
                if field_name not in ['estado', 'nueva_contraseña', 'confirmar_contraseña']:
                    # Se desactiva en UI pero no afecta validación si no es requerido
                    field.required = False
                    field.widget.attrs['disabled'] = 'disabled'
            else:
                if isinstance(field.widget, (forms.TextInput, forms.EmailInput, forms.PasswordInput)):
                    field.widget.attrs['readonly'] = 'readonly'
                elif isinstance(field.widget, forms.Select):
                    field.widget.attrs['disabled'] = 'disabled'
                elif isinstance(field.widget, forms.CheckboxInput):
                    field.widget.attrs['disabled'] = 'disabled'

    def clean(self):
        cleaned_data = super().clean()
        nueva = cleaned_data.get('nueva_contraseña')
        confirmar = cleaned_data.get('confirmar_contraseña')

        if self.is_guest:
            # Evitamos validación de campos no modificables
            return cleaned_data

        if nueva or confirmar:
            if nueva != confirmar:
                self.add_error('confirmar_contraseña', 'Las contraseñas no coinciden.')
            elif len(nueva) < 8:
                self.add_error('nueva_contraseña', 'La nueva contraseña debe tener al menos 8 caracteres.')

        return cleaned_data