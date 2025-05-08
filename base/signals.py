from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import Modulo, Accion

@receiver(post_migrate)
def insertar_datos_base(sender, **kwargs):
    # Insertar módulos si no existen
    if not Modulo.objects.exists():
        Modulo.objects.create(nombre="Login")        
        Modulo.objects.create(nombre="Usuarios")
        Modulo.objects.create(nombre="Productos")
        Modulo.objects.create(nombre="Entradas")
        Modulo.objects.create(nombre="Salidas")
        Modulo.objects.create(nombre="Reportes")
        Modulo.objects.create(nombre="Auditoría")

    # Insertar acciones si no existen
    if not Accion.objects.exists():
        Accion.objects.create(nombre="Iniciar Sesión")
        Accion.objects.create(nombre="Cerrar Sesión")        
        Accion.objects.create(nombre="Crear")
        Accion.objects.create(nombre="Editar")
        Accion.objects.create(nombre="Eliminar")
        Accion.objects.create(nombre="Ver")
        Accion.objects.create(nombre="Exportar")
