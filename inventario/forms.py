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
            'color', 'tiene_serie', 'numero_serie',
            'descripcion', 'nota', 'costo_unitario',
            'estado', 'stock',
        ]
        labels = {
            'tipo':           'Tipo',
            'nombre':         'Nombre',
            'modelo':         'Modelo',
            'marca':          'Marca',
            'color':          'Color',
            'tiene_serie':    '¿Este producto tendrá unidades con serie (hijos)?',
            'numero_serie':   'Número de serie',
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
            'nota':           forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'costo_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'estado':         forms.HiddenInput(),
            'stock':          forms.HiddenInput(),
        }

    def __init__(self, *args, crear=False, **kwargs):
        initial  = kwargs.pop('initial', {}) or {}
        instance = kwargs.get('instance', None)
        if instance and instance.pk and instance.marca:
            initial['marca'] = instance.marca.nombre
        kwargs['initial'] = initial
        super().__init__(*args, **kwargs)

        # Widgets comunes
        marcas = Marca.objects.order_by('nombre').values_list('nombre', flat=True)
        self.marcas_list = list(marcas)
        self.fields['marca'].widget = forms.Select(
            choices=[('', '---------')] + [(m, m) for m in self.marcas_list],
            attrs={'class': 'form-control select2-tags'}
        )
        self.fields['tipo'].queryset = Tipo.objects.filter(estado=True).order_by('nombre')
        self.fields['tiene_serie'] = forms.TypedChoiceField(
            choices=[('False', 'No'), ('True', 'Sí')],
            coerce=lambda v: v == 'True',
            empty_value=False,
            required=False,
            widget=forms.Select(attrs={'class':'form-control'})
        )

        # CASO HIJO: sólo nota y número de serie editables
        if instance and instance.pk and instance.producto_padre:
            # ocultar “¿Tiene Serie?”
            self.fields['tiene_serie'].widget = forms.HiddenInput()
            # deshabilitar todo excepto ‘numero_serie’ y ‘nota’
            for fname, field in self.fields.items():
                if fname not in ('numero_serie', 'nota'):
                    field.disabled = True
            # mostrar siempre el campo de número de serie
            self.fields['numero_serie'].widget   = forms.TextInput(attrs={'class':'form-control'})
            self.fields['numero_serie'].required = True
            return

        # CASO CREACIÓN o EDICIÓN DE PADRE

        # “tiene_serie” inicial y visibilidad
        if crear:
            self.fields['tiene_serie'].initial = False
        elif instance and instance.pk:
            self.fields['tiene_serie'].initial = instance.tiene_serie
            if instance.stock > 0 or instance.productos_hijos.exists():
                self.fields['tiene_serie'].widget = forms.HiddenInput()
                if instance.productos_hijos.exists():
                    self.fields['tiene_serie'].disabled = True

        # “estado”
        if crear:
            self.fields['estado'].initial = True
            self.fields['estado'].widget  = forms.HiddenInput()
        else:
            if instance and instance.pk and instance.stock == 0:
                self.fields['estado'].widget = forms.Select(
                    choices=[(True, 'Activo'), (False, 'Inactivo')],
                    attrs={'class':'form-control'}
                )
            else:
                self.fields['estado'].widget = forms.HiddenInput()

        # “numero_serie” siempre oculto para padres/creación
        self.fields['numero_serie'].widget   = forms.HiddenInput()
        self.fields['numero_serie'].required = False

        # Aplicar form-control al resto de campos
        for fname, fld in self.fields.items():
            if fname not in ('tipo','marca','tiene_serie','numero_serie','estado','stock'):
                fld.widget.attrs.update({'class':'form-control'})

    def clean_marca(self):
        texto = self.cleaned_data['marca'].strip()
        if not texto:
            raise forms.ValidationError("La marca es obligatoria.")
        if not re.match(r'^[A-Za-z0-9áéíóúÁÉÍÓÚñÑ\s]+$', texto):
            raise forms.ValidationError("La marca solo puede contener letras y números.")
        marca_obj, _ = Marca.objects.get_or_create(
            nombre__iexact=texto,
            defaults={'nombre': texto}
        )
        return marca_obj

    def clean_nombre(self):
        if self.instance.pk and self.instance.producto_padre:
            return self.instance.nombre

        nombre = self.cleaned_data.get('nombre','').strip()
        tipo   = self.cleaned_data.get('tipo')
        if not nombre:
            raise forms.ValidationError("El nombre es obligatorio.")
        if not re.match(r'^[A-Za-z0-9áéíóúÁÉÍÓÚñÑ\s]+$', nombre):
            raise forms.ValidationError("Sólo letras, números y espacios.")

        qs = Producto.objects.filter(
            nombre__iexact=nombre,
            tipo=tipo,
            producto_padre__isnull=True
        )
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Ya existe un producto con ese nombre y tipo.")
        return nombre

    def clean_costo_unitario(self):
        costo = self.cleaned_data.get('costo_unitario')
        if costo is None or costo < 0:
            raise forms.ValidationError("El costo unitario no puede ser negativo.")
        return costo

    def clean_color(self):
        color = self.cleaned_data.get('color', '').strip()
        if not color:
            raise forms.ValidationError("El color es obligatorio.")
        if not re.fullmatch(r"[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+", color):
            raise forms.ValidationError("El color solo debe contener letras y espacios.")
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
    numero_serie = forms.CharField(
        required=False,
        label='N.º Serie',
        widget=forms.TextInput(attrs={
            'class': 'form-control numero-serie-input',
            'placeholder': 'N.º Serie'
        })
    )
    class Meta:
        model = EntradaLinea
        fields = ['producto','numero_serie', 'cantidad']
        labels = {
            'producto': 'Producto',
            'numero_serie': 'N.º Serie',
            'cantidad': 'Cantidad',
        }
        widgets = {
            'producto': forms.Select(attrs={'class': 'form-control select-producto-auto select2-tipo', 'data-placeholder': 'Selecciona producto…'}),
            'numero_serie': forms.TextInput(attrs={'class': 'form-control numero-serie-input', 'placeholder': 'N.º Serie'}),
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
        self.fields['cantidad'].required = False

    def clean(self):
        cd = super().clean()
        prod = cd.get('producto')
        serie = cd.get('numero_serie')
        qty   = cd.get('cantidad')

        # Si el padre ya tiene hijos, exigir serie
        if prod and prod.productos_hijos.exists() and not serie:
            raise forms.ValidationError(
                "Este producto ya tiene unidades con serie; ingresa un número de serie."
            )

        # Si hay serie → qty = 1
        if prod and prod.numero_serie:
            cd['cantidad'] = 1

        return cd

    def clean_cantidad(self):
        cantidad = self.cleaned_data.get('cantidad')
        if cantidad in (None, ''):
            return 1  # Asume 1 si viene vacío (como en productos hijos)
        if cantidad <= 0:
            raise forms.ValidationError("La cantidad debe ser mayor que cero.")
        return cantidad

    def clean_numero_serie(self):
        numero_serie = self.cleaned_data.get('numero_serie','').strip()
        if numero_serie:
            qs = Producto.objects.filter(numero_serie=numero_serie)
            # Si estamos editando una línea que ya apuntaba a ese hijo, lo permitimos:
            if self.instance.pk and self.instance.producto.numero_serie == numero_serie:
                return numero_serie
            if qs.exists():
                raise ValidationError("Ya existe un producto con este número de serie.")
        return numero_serie

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