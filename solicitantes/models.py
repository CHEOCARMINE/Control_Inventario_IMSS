from django.db import models

class Departamento(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    estado = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

class Unidad(models.Model):
    nombre = models.CharField(max_length=150, unique=True)
    clues = models.CharField(max_length=20, unique=True)
    direccion = models.TextField()
    departamentos = models.ManyToManyField(Departamento, related_name='unidades')
    estado = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} ({self.clues})"

class Cargo(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre

class Solicitante(models.Model):
    nombre     = models.CharField(max_length=100, unique=True)
    cargo      = models.ForeignKey(Cargo, on_delete=models.PROTECT)
    unidad     = models.ForeignKey(Unidad, on_delete=models.CASCADE)
    departamento = models.ForeignKey(Departamento, on_delete=models.PROTECT, help_text="Departamento dentro de la unidad seleccionada")
    estado     = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

