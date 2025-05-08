from django.db import models

# Create your models here.
class DatosPersonales(models.Model):
    nombres           = models.CharField(max_length=100, null=True, blank=True)
    apellido_paterno  = models.CharField(max_length=100, null=True, blank=True)
    apellido_materno = models.CharField(max_length=100, null=True, blank=True)
    correo            = models.EmailField(max_length=150, null=True, blank=True)
    numero_empleado   = models.CharField(max_length=50, unique=True, null=True, blank=True)
    telefono          = models.CharField(max_length=20, null=True, blank=True)
    fecha_registro    = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombres} {self.apellido_paterno}"