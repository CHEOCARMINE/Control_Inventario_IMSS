import re
from django import forms
from .models import Departamento, Unidad

# Formulario Departamentos
class DepartamentoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        crear = kwargs.pop('crear', False)
        super().__init__(*args, **kwargs)
        if crear:
            self.fields.pop('estado')

    class Meta:
        model = Departamento
        fields = ['nombre', 'estado']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del departamento'
            }),
            'estado': forms.Select(choices=[
                (True, 'Activo'),
                (False, 'Inactivo')
            ], attrs={'class': 'form-control'})
        }
        labels = {
            'nombre': 'Nombre del departamento',
            'estado': 'Estado'
        }

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre', '')
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', nombre):
            raise forms.ValidationError('El nombre solo puede contener letras y espacios.')
        return nombre

# Formulario Unidades
class UnidadForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        crear = kwargs.pop('crear', False)
        super().__init__(*args, **kwargs)
        if crear:
            self.fields.pop('estado')

    class Meta:
        model = Unidad
        fields = ['nombre', 'direccion', 'clues', 'departamentos', 'estado']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la unidad'
            }),
            'direccion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Dirección de la unidad'
            }),
            'clues': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Formato ABCD123456'
            }),
            'departamentos':  forms.SelectMultiple(attrs={'class': 'form-control select2', 'style': 'width:100%'}),
            'estado': forms.Select(choices=[(True, 'Activo'), (False, 'Inactivo')], attrs={'class': 'form-control'})
        }
        labels = {
            'departamentos': 'Departamentos asignados',
            'clues': 'CLUES',
            'direccion': 'Dirección',
            'estado': 'Estado'
        }

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre', '')
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', nombre):
            raise forms.ValidationError('El nombre solo puede contener letras y espacios.')
        return nombre

    def clean_direccion(self):
        direccion = self.cleaned_data.get('direccion', '')
        if not re.match(r'^[a-zA-Z0-9\s\.,#\-áéíóúÁÉÍÓÚñÑ]+$', direccion):
            raise forms.ValidationError('La dirección contiene caracteres inválidos.')
        return direccion

    def clean_clues(self):
        clues = self.cleaned_data.get('clues', '')
        # Validación del formato: 5 letras mayúsculas + 6 dígitos (ej: ABCDE123456)
        if not re.match(r'^[A-Z]{5}\d{6}$', clues):
            raise forms.ValidationError('Formato CLUES inválido (ej: ABCDE123456).')
        return clues