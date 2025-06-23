import re
from django import forms
from datetime import date
from django.utils.html import format_html
from django.core.exceptions import ValidationError
from .models import Tipo, Producto, Entrada, EntradaLinea
from django.forms import formset_factory, modelformset_factory
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
            'Subcatalogo':   forms.Select(attrs={'class': 'form-control select2-subcategoria'}),
            'unidad_medida': forms.Select(attrs={'class': 'form-control select2-unidad'}),
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
    marca = forms.CharField(label="Marca")

    class Meta:
        model = Producto
        fields = [
            'tipo', 'nombre', 'modelo', 'marca',
            'color', 'numero_serie', 'descripcion',
            'nota', 'costo_unitario', 'estado', 'stock',
        ]
        labels = {
            'tipo':           'Tipo',
            'nombre':         'Nombre',
            'modelo':         'Modelo',
            'marca':          'Marca',
            'color':          'Color',
            'descripcion':    'Descripción',
            'nota':           'Nota',
            'costo_unitario': 'Costo unitario',
            'estado':         'Estado',
            'stock':          'Stock',
        }
        widgets = {
            'tipo':           forms.Select(attrs={'class': 'form-control select2-tipo'}),
            'nombre':         forms.TextInput(attrs={'class': 'form-control'}),
            'modelo':         forms.TextInput(attrs={'class': 'form-control'}),
            'color':          forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion':    forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'nota':           forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'costo_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'estado':         forms.HiddenInput(),
            'stock':          forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        # Extraemos el flag 'crear'
        crear = kwargs.pop('crear', False)

        # Ajustamos initial para precargar marca al editar
        initial = kwargs.pop('initial', {}) or {}
        instance = kwargs.get('instance')
        if instance and instance.pk and instance.marca:
            initial['marca'] = instance.marca.nombre
        kwargs['initial'] = initial

        super().__init__(*args, **kwargs)

        # Construimos la lista de nombres de Marca
        marcas = Marca.objects.order_by('nombre')\
            .values_list('nombre', flat=True)
        self.marcas_list = list(marcas)

        # Reemplazamos el widget de 'marca' por un <select>
        choices = [('', '---------')] + [(m, m) for m in self.marcas_list]
        self.fields['marca'].widget = forms.Select(
            choices=choices,
            attrs={'class': 'form-control select2-tags'}
        )

        # Ajustes de campos restantes
        self.fields['tipo'].queryset = Tipo.objects.filter(estado=True)\
            .order_by('nombre')
        for fname, fld in self.fields.items():
            if fname not in ('tipo', 'marca'):
                fld.widget.attrs.update({'class': 'form-control'})

        # Control de ocultar/mostrar stock y estado
        if crear:
            self.fields['estado'].initial = True
            self.fields['estado'].widget = forms.HiddenInput()
            self.fields['stock'].widget  = forms.HiddenInput()
        else:
            self.fields['stock'].widget = forms.HiddenInput()
            if instance and instance.pk and instance.stock == 0:
                self.fields['estado'].widget = forms.Select(
                    choices=[(True, 'Activo'), (False, 'Inactivo')],
                    attrs={'class': 'form-control'}
                )
            else:
                self.fields['estado'].widget = forms.HiddenInput()

    def clean_marca(self):
        texto = self.cleaned_data['marca'].strip()
        if not texto:
            raise forms.ValidationError("La marca es obligatoria.")
        # Validar solo letras y números
        if not re.match(r'^[A-Za-z0-9áéíóúÁÉÍÓÚñÑ\s]+$', texto):
            raise forms.ValidationError("La marca solo puede contener letras y números.")
        # Buscamos case‐insensitive o creamos
        marca_obj, _ = Marca.objects.get_or_create(
            nombre__iexact=texto,
            defaults={'nombre': texto}
        )
        return marca_obj

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre', '').strip()
        tipo   = self.cleaned_data.get('tipo')
        if not nombre:
            raise forms.ValidationError("El nombre es obligatorio.")
        if not re.match(r'^[A-Za-z0-9áéíóúÁÉÍÓÚñÑ\s]+$', nombre):
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

    def clean_color(self):
        color = self.cleaned_data.get('color', '').strip()
        if not color:
            raise ValidationError("El color es obligatorio.")
        if not re.fullmatch(r"[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+", color):
            raise ValidationError("El color solo debe contener letras y espacios.")
        return color

# FORMULARIO PARA LA CABECERA DE ENTRADA
class EntradaForm(forms.ModelForm):
    class Meta:
        model = Entrada
        fields = ['folio', 'fecha_recepcion']
        labels = {
            'folio':          'Folio (opcional)',
            'fecha_recepcion': 'Fecha de Recepción',
        }
        widgets = {
            'folio': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'AAAA/BBB/0001/2025 (opcional)'
            }),
            'fecha_recepcion': forms.DateInput(
                format='%Y-%m-%d',
                attrs={
                    'type': 'date',
                    'class': 'form-control'
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer folio opcional
        self.fields['folio'].required = False

    def clean_folio(self):
        folio = (self.cleaned_data.get('folio') or '').strip()
        if not folio:
            return None

        año_actual = date.today().year
        pattern = rf'^[A-Z]{{4}}/[A-Z]{{3}}/[0-9]{{4}}/{año_actual}$'
        if not re.match(pattern, folio):
            raise ValidationError(
                f"El folio debe tener el formato AAAA/BBB/0001/{año_actual} "
                "con letras mayúsculas y dígitos según corresponda."
            )

        qs = Entrada.objects.filter(folio=folio)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Ya existe una entrada con este folio.")
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
            'producto': forms.Select(attrs={'class': 'form-control select-producto-auto select2-tipo'}),
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

EntradaLineaFormSetRegistro = modelformset_factory(
    EntradaLinea,
    form=EntradaLineaForm,
    extra=1,
    can_delete=True
)

EntradaLineaFormSetEdicion = modelformset_factory(
    EntradaLinea,
    form=EntradaLineaForm,
    extra=0,          
    can_delete=True
)