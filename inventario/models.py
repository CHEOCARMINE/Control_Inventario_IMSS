from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import F, Q, UniqueConstraint
from auxiliares_inventario.models import Catalogo, Subcatalogo, UnidadDeMedida, Marca

class Tipo(models.Model):
    nombre        = models.CharField(max_length=100)
    Subcatalogo   = models.ForeignKey(Subcatalogo, on_delete=models.CASCADE)
    unidad_medida = models.ForeignKey(UnidadDeMedida, on_delete=models.CASCADE)
    stock_minimo  = models.PositiveIntegerField()
    estado        = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

    @property
    def categoria(self):
        return self.Subcatalogo.catalogo

class Producto(models.Model):
    tipo           = models.ForeignKey(Tipo, on_delete=models.CASCADE)
    nombre         = models.CharField(max_length=100)
    modelo         = models.CharField(max_length=50)
    marca          = models.ForeignKey(Marca, on_delete=models.PROTECT)
    color          = models.CharField(max_length=30)
    tiene_serie    = models.BooleanField(default=False, verbose_name="¿Este producto tendrá unidades con serie (hijos)?")
    numero_serie   = models.CharField(max_length=100, unique=True, blank=True, null=True, verbose_name="Número de serie")
    descripcion    = models.TextField(blank=True)
    nota           = models.TextField(blank=True)
    costo_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    estado         = models.BooleanField(default=True)
    stock          = models.PositiveIntegerField(default=0)
    producto_padre = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name='productos_hijos')

    class Meta:
        constraints = [
            # Un hijo debe tener numero_serie y producto_padre; un padre NO
            models.CheckConstraint(
                check=(
                    (Q(numero_serie__isnull=False) & Q(producto_padre__isnull=False)) |
                    (Q(numero_serie__isnull=True)  & Q(producto_padre__isnull=True))
                ),
                name='producto_parent_child_consistency'
            ),
        ]

    def clean(self):
        # Si pongo numero_serie, forzar que el padre tenga tiene_serie=True
        if self.producto_padre and not self.producto_padre.tiene_serie:
            raise ValidationError(
                "No puedes asignar hijo a un producto que no está marcado como 'tiene serie'."
            )

    def save(self, *args, **kwargs):
        # Si se crea un hijo, marcar siempre al padre con tiene_serie=True
        if self.producto_padre:
            self.producto_padre.tiene_serie = True
            self.producto_padre.save(update_fields=['tiene_serie'])
        super().save(*args, **kwargs)

    def __str__(self):
        if self.numero_serie:
            return f"{self.tipo.nombre} – {self.nombre} (Serie: {self.numero_serie})"
        return f"{self.tipo.nombre} – {self.nombre}"

class Entrada(models.Model):
    folio         = models.CharField(max_length=30, blank=True, null=True)
    fecha_recepcion  = models.DateField()
    fecha_entrada = models.DateField(auto_now_add=True)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['folio'],
                condition=~Q(folio=''),
                name='unique_folio_nonblank'
            ),
        ]

    def __str__(self):
        folio_display = self.folio or 'Pendiente'
        return f"{folio_display} – {self.fecha_entrada}"

class EntradaLinea(models.Model):
    entrada  = models.ForeignKey(Entrada, on_delete=models.CASCADE, related_name='lineas')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.entrada.folio} – {self.producto.nombre} ({self.cantidad})"
