import re
from django import forms
from django.forms import formset_factory
from django.utils.html import format_html
from django.core.exceptions import ValidationError
from .models import Tipo, Producto, Entrada, EntradaLinea
from auxiliares_inventario.models import Subcatalogo, UnidadDeMedida, Marca

# Tipo FORM
class TipoForm(forms.ModelForm):

    def __init__(self, *args, crear=False, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['Subcatalogo'].queryset = Subcatalogo.objects.filter(estado=True)

        self.fields['unidad_medida'].queryset = UnidadDeMedida.objects.all()

        if crear:
            self.fields['estado'].initial = True
            self.fields['estado'].widget  = forms.HiddenInput()
        else:
            self.fields['estado'].widget = forms.Select(
                choices=[(True, 'Activo'), (False, 'Inactivo')],
                attrs={'class': 'form-control'}
            )

    class Meta:
        model  = Tipo
        fields = ['nombre', 'Subcatalogo', 'unidad_medida', 'stock_minimo', 'estado']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la tipo'
            }),
            'Subcatalogo':   forms.Select(attrs={'class': 'form-control'}),
            'unidad_medida': forms.Select(attrs={'class': 'form-control'}),
            'stock_minimo':  forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
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
        qs = Tipo.objects.filter(nombre__iexact=nombre)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Ya existe una tipo con ese nombre.")
        return nombre

# FORMULARIO PARA CREAR / EDITAR UN PRODUCTO
class ProductoForm(forms.ModelForm):
    def __init__(self, *args, crear=False, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['tipo'].queryset = Tipo.objects.filter(
            estado=True
        ).order_by('nombre')
        self.fields['marca'].queryset = Marca.objects.all().order_by('nombre')

        for nombre_campo, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})

        if crear:
            self.fields['estado'].initial = True
            self.fields['estado'].widget = forms.HiddenInput()
            self.fields['stock'].widget = forms.HiddenInput()
        else:
            self.fields['stock'].widget = forms.HiddenInput()

            if self.instance and self.instance.pk and self.instance.stock == 0:
                self.fields['estado'].widget = forms.Select(
                    choices=[(True, 'Activo'), (False, 'Inactivo')],
                    attrs={'class': 'form-control'}
                )
            else:
                self.fields['estado'].widget = forms.HiddenInput()

    class Meta:
        model = Producto
        fields = [
            'tipo',
            'nombre',
            'modelo',
            'marca',
            'color',
            'numero_serie',
            'descripcion',
            'nota',
            'costo_unitario',
            'estado',
            'stock',
        ]
        labels = {
            'tipo':           'Tipo',
            'nombre':         'Nombre',
            'modelo':         'Modelo',
            'marca':          'Marca',
            'color':          'Color',
            'numero_serie':   'Número de serie',
            'descripcion':    'Descripción',
            'nota':           'Nota',
            'costo_unitario': 'Costo unitario',
            'estado':         'Estado',
            'stock':          'Stock',
        }
        widgets = {
            'descripcion':    forms.Textarea(attrs={'rows': 3}),
            'nota':           forms.Textarea(attrs={'rows': 2}),
            'costo_unitario': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre', '').strip()
        tipo = self.cleaned_data.get('tipo')
        if not nombre:
            raise forms.ValidationError("El nombre es obligatorio.")
        if not re.match(r'^[\w\sáéíóúÁÉÍÓÚñÑ]+$', nombre):
            raise forms.ValidationError("Sólo letras, números y espacios.")
        qs = Producto.objects.filter(nombre__iexact=nombre, tipo=tipo)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Ya existe un producto con ese nombre y tipo.")
        return nombre

    def clean_costo_unitario(self):
        costo = self.cleaned_data.get('costo_unitario')
        if costo is None:
            return costo
        if costo < 0:
            raise forms.ValidationError("El costo unitario no puede ser negativo.")
        return costo

# FORMULARIO PARA LA CABECERA DE ENTRADA
class EntradaForm(forms.ModelForm):
    class Meta:
        model = Entrada
        fields = ['folio', 'fecha_folio']
        labels = {
            'folio':       'Folio',
            'fecha_folio': 'Fecha de Folio',
        }
        widgets = {
            'folio': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Folio de la entrada'
            }),
            'fecha_folio': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
        }

    def clean_folio(self):
        folio = self.cleaned_data.get('folio', '').strip()
        if not folio:
            raise forms.ValidationError("El folio es obligatorio.")
        pattern = r'^[A-Za-z0-9\-]+$'
        if not re.match(pattern, folio):
            raise forms.ValidationError(
            )
        return folio

# FORMULARIO PARA CADA LÍNEA DE ENTRADA
class EntradaLineaForm(forms.ModelForm):
    class Meta:
        model = EntradaLinea
        fields = ['producto', 'cantidad']
        labels = {
            'producto': 'Producto',
            'cantidad': 'Cantidad',
        }
        widgets = {
            'producto': forms.Select(attrs={'class': 'form-control select-producto-auto'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'placeholder': 'Cantidad'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['producto'].label_from_instance = lambda obj: format_html(
            '{} / {} / {} / {}{}',
            obj.nombre,
            obj.marca.nombre,
            obj.modelo,
            obj.color,
            (f' / {obj.numero_serie}' if obj.numero_serie else '')
        )

    def clean_cantidad(self):
        cantidad = self.cleaned_data.get('cantidad')
        if cantidad is None or cantidad <= 0:
            raise forms.ValidationError("La cantidad debe ser mayor que cero.")
        return cantidad

EntradaLineaFormSet = formset_factory(
    EntradaLineaForm,
    extra=1,
    can_delete=True
)