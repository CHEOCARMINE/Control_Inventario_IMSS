import re
from django import forms
from .models import Departamento, Unidad, Solicitante, Cargo

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

        # Sólo departamentos activos
        self.fields['departamentos'].queryset = Departamento.objects.filter(
            estado=True
        ).order_by('nombre')

        # Oculta estado al crear
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
                'placeholder': 'Formato ABCDE123456'
            }),
            'departamentos': forms.SelectMultiple(attrs={
                'class': 'form-control select2',
                'style': 'width:100%'
            }),
            'estado': forms.Select(choices=[
                (True, 'Activo'),
                (False, 'Inactivo')
            ], attrs={'class': 'form-control'})
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
        if not re.match(r'^[a-zA-Z0-9\s\.,#\-\áéíóúÁÉÍÓÚñÑ]+$', direccion):
            raise forms.ValidationError('La dirección contiene caracteres inválidos.')
        return direccion

    def clean_clues(self):
        clues = self.cleaned_data.get('clues', '')
        if not re.match(r'^[A-Z]{5}\d{6}$', clues):
            raise forms.ValidationError('Formato CLUES inválido (ej: ABCDE123456).')
        return clues


# Formulario Solicitantes
class SolicitanteForm(forms.ModelForm):
    class Meta:
        model = Solicitante
        fields = ['nombre', 'cargo', 'unidad', 'departamento', 'estado']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre completo'
            }),
            'cargo': forms.Select(attrs={'class': 'form-control'}),
            'unidad': forms.Select(attrs={'class': 'form-control'}),
            'departamento': forms.Select(attrs={'class': 'form-control'}),
            'estado': forms.Select(choices=[
                (True, 'Activo'),
                (False, 'Inactivo')
            ], attrs={'class': 'form-control'}),
        }
        labels = {
            'nombre': 'Nombre completo',
            'cargo': 'Cargo',
            'unidad': 'Unidad',
            'departamento': 'Departamento',
            'estado': 'Estado'
        }

    def __init__(self, *args, **kwargs):
        crear = kwargs.pop('crear', False)
        super().__init__(*args, **kwargs)

        # Ocultar estado al crear
        if crear:
            self.fields.pop('estado')

        # Sólo unidades activas
        self.fields['unidad'].queryset = Unidad.objects.filter(
            estado=True
        ).order_by('nombre')

        # Departamento inicialmente vacío
        self.fields['departamento'].queryset = Departamento.objects.none()

        if self.instance.pk:
            # al editar: departamentos activos de la unidad
            self.fields['departamento'].queryset = (
                self.instance.unidad.departamentos.filter(estado=True).order_by('nombre'))
        elif 'unidad' in self.data:
            # AJAX POST
            try:
                uid = int(self.data.get('unidad'))
                unidad = Unidad.objects.get(pk=uid, estado=True)
                self.fields['departamento'].queryset = (unidad.departamentos.filter(estado=True).order_by('nombre'))
            except (ValueError, Unidad.DoesNotExist):
                pass

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre', '')
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', nombre):
            raise forms.ValidationError('El nombre sólo puede contener letras y espacios.')
        return nombre