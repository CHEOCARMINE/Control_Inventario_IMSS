from django.db import models
from inventario.models import Producto
from solicitantes.models import Solicitante, Unidad, Departamento

class ValeSalida(models.Model):
    folio = models.CharField(max_length=30, unique=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_entrega = models.DateTimeField(blank=True, null=True)
    solicitante = models.ForeignKey(Solicitante, on_delete=models.PROTECT)
    unidad = models.ForeignKey(Unidad, on_delete=models.PROTECT)
    departamento = models.ForeignKey(Departamento, on_delete=models.PROTECT)
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('entregado', 'Entregado'),
        ('cancelado', 'Cancelado'),
    ]
    estado = models.CharField(max_length=15, choices=ESTADOS, default='pendiente')
    motivo_cancelacion = models.TextField(blank=True, null=True)
    vale_pdf = models.FileField(upload_to='vales_pdf/', blank=True, null=True)

    def __str__(self):
        return f"Vale {self.folio or '(sin folio)'} – {self.get_estado_display()}"


class ValeDetalle(models.Model):
    vale = models.ForeignKey(ValeSalida, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.producto} – {self.cantidad} pzas"