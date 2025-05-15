from django import forms
from .models import Departamento

class DepartamentoForm(forms.ModelForm):
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

