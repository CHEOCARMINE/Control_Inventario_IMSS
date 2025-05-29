import re
from django import forms
from .models import Herencia
from auxiliares_inventario.models import Subcatalogo, UnidadDeMedida

class HerenciaForm(forms.ModelForm):
    def __init__(self, *args, crear=False, **kwargs):
        super().__init__(*args, **kwargs)

        # 1) Filtrar sólo Subcatalogos activos
        self.fields['Subcatalogo'].queryset = Subcatalogo.objects.filter(estado=True)
        # 2) Todas las Unidades de medida
        self.fields['unidad_medida'].queryset = UnidadDeMedida.objects.all()

        if crear:
            # Al crear: presetear estado=True y ocultar el campo
            self.fields['estado'].initial = True
            self.fields['estado'].widget  = forms.HiddenInput()
        else:
            # Al editar: mostrar select de estado
            self.fields['estado'].widget = forms.Select(
                choices=[(True, 'Activo'), (False, 'Inactivo')],
                attrs={'class': 'form-control'}
            )

    class Meta:
        model  = Herencia
        fields = ['nombre', 'Subcatalogo', 'unidad_medida', 'stock_minimo', 'estado']
        widgets = {
            'nombre':        forms.TextInput(attrs={
                                    'class': 'form-control',
                                    'placeholder': 'Nombre de la herencia'
                                }),
            'Subcatalogo':   forms.Select(attrs={'class': 'form-control'}),
            'unidad_medida': forms.Select(attrs={'class': 'form-control'}),
            'stock_minimo':  forms.NumberInput(attrs={
                                    'class': 'form-control',
                                    'min': 0
                                }),
            # 'estado' se gestiona en __init__
        }
        labels = {
            'Subcatalogo':   'Subcategoría',
            'unidad_medida': 'Unidad de medida',
            'stock_minimo':  'Stock mínimo',
        }

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre'].strip()
        if not re.match(r'^[\w\sáéíóúÁÉÍÓÚñÑ]+$', nombre):
            raise forms.ValidationError("Sólo letras, números y espacios.")
        qs = Herencia.objects.filter(nombre__iexact=nombre)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Ya existe una herencia con ese nombre.")
        return nombre
