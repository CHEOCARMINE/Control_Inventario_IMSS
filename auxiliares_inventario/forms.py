import re
from django import forms
from .models import Catalogo

class CatalogoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        crear = kwargs.pop('crear', False)
        super().__init__(*args, **kwargs)
        # Oculta el campo 'estado' cuando estamos creando una nueva categoría
        if crear:
            self.fields.pop('estado')

    class Meta:
        model = Catalogo
        fields = ['nombre', 'estado']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la categoría'
            }),
            'estado': forms.Select(choices=[
                (True, 'Activo'),
                (False, 'Inactivo')
            ], attrs={'class': 'form-control'})
        }
        labels = {
            'nombre': 'Nombre de la categoría',
            'estado': 'Estado'
        }

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre', '').strip()
        # Validación: solo letras y espacios
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', nombre):
            raise forms.ValidationError('El nombre solo puede contener letras y espacios.')
        # Validación: unicidad (case-insensitive), excluyendo la instancia actual al editar
        qs = Catalogo.objects.filter(nombre__iexact=nombre)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Ya existe una categoría con ese nombre.')
        return nombre