from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.db import connection

@receiver(post_migrate)
def insertar_datos_base(sender, **kwargs):
    # Verifica si la tabla base_modulo existe
    with connection.cursor() as cursor:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='base_modulo'")
        tabla_modulo_existe = cursor.fetchone()

    if tabla_modulo_existe:
        from .models import Modulo
        if not Modulo.objects.exists():
            Modulo.objects.create(nombre="Login")        
            Modulo.objects.create(nombre="Usuarios")
            Modulo.objects.create(nombre="Productos")
            Modulo.objects.create(nombre="Entradas")
            Modulo.objects.create(nombre="Salidas")
            Modulo.objects.create(nombre="Reportes")
            Modulo.objects.create(nombre="Auditoría")

    # Verifica si la tabla base_accion existe
    with connection.cursor() as cursor:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='base_accion'")
        tabla_accion_existe = cursor.fetchone()

    if tabla_accion_existe:
        from .models import Accion
        if not Accion.objects.exists():
            Accion.objects.create(nombre="Iniciar Sesión")
            Accion.objects.create(nombre="Cerrar Sesión")        
            Accion.objects.create(nombre="Crear")
            Accion.objects.create(nombre="Editar")
            Accion.objects.create(nombre="Eliminar")
            Accion.objects.create(nombre="Ver")
            Accion.objects.create(nombre="Exportar")
