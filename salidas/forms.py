import json
from django import forms
from solicitantes.models import Solicitante, Unidad, Departamento
from .models import ValeSalida

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
