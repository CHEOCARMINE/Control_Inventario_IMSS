from django.db import models

class Modulo(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre

class Accion(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre

class ReferenciasLog(models.Model):
    tabla = models.CharField(max_length=100)
    id_registro = models.IntegerField()

    def __str__(self):
        return f"{self.tabla} - ID {self.id_registro}"

class LogsSistema(models.Model):
    id_dato = models.IntegerField()  
    id_modulo = models.ForeignKey(Modulo, on_delete=models.CASCADE)
    id_accion = models.ForeignKey(Accion, on_delete=models.CASCADE)
    id_ref_log = models.ForeignKey(ReferenciasLog, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_evento = models.DateTimeField(auto_now_add=True)
    ip_origen = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Log ID {self.id_log} - Dato {self.id_dato} en {self.fecha_evento}"
