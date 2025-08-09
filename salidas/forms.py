import json
from django import forms
from .models import ValeSalida
from .models import ValeDetalle
from django.forms import modelformset_factory
from solicitantes.models import Solicitante, Unidad, Departamento

# Formulario para registrar una salida de productos
class ValeSalidaForm(forms.Form):
    solicitante = forms.ModelChoiceField(
        queryset=Solicitante.objects.filter(estado=True),
        label="Solicitante",
        required=True
    )
    unidad = forms.ModelChoiceField(
        queryset=Unidad.objects.filter(estado=True),
        label="Unidad",
        required=True
    )
    departamento = forms.ModelChoiceField(
        queryset=Departamento.objects.filter(estado=True),
        label="Departamento",
        required=True
    )
    carrito_json = forms.CharField(
        widget=forms.HiddenInput,
        required=True
    )

    # Validación del JSON del carrito
    def clean_carrito_json(self):
        data = self.cleaned_data.get('carrito_json', '')
        try:
            carrito = json.loads(data)
        except (ValueError, TypeError):
            raise forms.ValidationError("Formato de carrito inválido.")
        if not isinstance(carrito, list) or len(carrito) == 0:
            raise forms.ValidationError("Debe agregar al menos un producto al carrito.")
        for idx, item in enumerate(carrito, start=1):
            if not isinstance(item, dict):
                raise forms.ValidationError(f"Elemento #{idx} del carrito no es válido.")
            cantidad = item.get('cantidad')
            if cantidad is None or not isinstance(cantidad, int) or cantidad < 1:
                raise forms.ValidationError(
                    f"La cantidad del producto #{idx} debe ser un número entero mayor que cero."
                )
        return carrito

# Formulario para cancelar un vale de salida
class CancelarValeForm(forms.Form):
    motivo = forms.CharField(
        label='Motivo de cancelación',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Escribe aquí el motivo…',
            'required': True,
        })
    )

# Formulario para editar un vale de salida
class ValeSalidaFormEdicion(forms.ModelForm):
    solicitante = forms.ModelChoiceField(
        queryset=Solicitante.objects.filter(estado=True),
        label="Solicitante",
        widget=forms.Select(attrs={
            'class': 'form-control select2-solicitante',
        })
    )
    unidad = forms.ModelChoiceField(
        queryset=Unidad.objects.filter(estado=True),
        label="Unidad",
        widget=forms.Select(attrs={
            'class': 'form-control select2-unidad',
        })
    )
    departamento = forms.ModelChoiceField(
        queryset=Departamento.objects.filter(estado=True),
        label="Departamento",
        widget=forms.Select(attrs={
            'class': 'form-control select2-departamento',
        })
    )

    class Meta:
        model = ValeSalida
        fields = ['solicitante', 'unidad', 'departamento']

class ValeDetalleForm(forms.ModelForm):
    producto_hijo_id = forms.IntegerField(
        widget=forms.HiddenInput(),
        required=False
    )

    def __init__(self, *args, **kwargs):
        self.cantidad_original = kwargs.pop('cantidad_original', 0)
        super().__init__(*args, **kwargs)

    class Meta:
        model = ValeDetalle
        fields = ['producto', 'cantidad']
        widgets = {
            'producto': forms.Select(attrs={'class': 'form-control select2-producto-auto'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control cantidad-input'}),
        }

    def clean(self):
        from .models import Producto
        cleaned_data     = super().clean()
        hijo_id          = cleaned_data.get('producto_hijo_id')
        cantidad         = cleaned_data.get('cantidad')
        if hijo_id:
            try:
                producto = Producto.objects.get(pk=hijo_id)
            except Producto.DoesNotExist:
                self.add_error('cantidad', 'Producto hijo inválido.')
                return cleaned_data
        else:
            producto = cleaned_data.get('producto')
        if producto and not producto.tiene_serie:
            stock_total = producto.stock + self.cantidad_original
            if cantidad is None or cantidad < 1:
                self.add_error('cantidad', 'La cantidad debe ser mayor que cero.')
            elif cantidad > stock_total:
                self.add_error(
                    'cantidad',
                    f'La cantidad ({cantidad}) excede el stock disponible ({stock_total}).'
                )
        return cleaned_data

ValeDetalleFormSet = modelformset_factory(
    ValeDetalle,
    form=ValeDetalleForm,
    extra=0,
    can_delete=True,
    min_num=1,
    validate_min=True
)