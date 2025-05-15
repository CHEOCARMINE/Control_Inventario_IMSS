from django.db import models

# Create your models here.
class Departamento(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    estado = models.BooleanField(default=True)

class Unidad(models.Model):
    nombre = models.CharField(max_length=150)
    clues = models.CharField(max_length=20, unique=True)
    direccion = models.TextField()
    departamento = models.ForeignKey(Departamento, on_delete=models.PROTECT)
    estado = models.BooleanField(default=True)

class Solicitante(models.Model):
    nombre = models.CharField(max_length=100)
    cargo = models.CharField(max_length=100)
    unidad = models.ForeignKey(Unidad, on_delete=models.CASCADE)
    estado = models.BooleanField(default=True)
