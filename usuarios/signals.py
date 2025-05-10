from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.db import connection

def tabla_existe(nombre_tabla):
    """Verifica si una tabla existe en la base de datos."""
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=%s", [nombre_tabla]
        )
        return cursor.fetchone() is not None

@receiver(post_migrate)
def create_guest_datos(sender, **kwargs):
    """
    Al migrar la app 'usuarios', crea DatosPersonales
    con nombres='Invitado' y apellido_paterno igual al nombre del rol.
    """
    if sender.name != 'usuarios':
        return

    if not tabla_existe('login_app_rol') or not tabla_existe('usuarios_datospersonales'):
        return

    from login_app.models import Rol
    from usuarios.models import DatosPersonales

    for rol in Rol.objects.all():
        DatosPersonales.objects.get_or_create(
            nombres='Invitado',
            apellido_paterno=rol.nombre,
            defaults={
                'apellido_materno': 'Invitado',
                'correo': None,
                'numero_empleado': None,
                'telefono': None,
                # fecha_registro se autogenera con auto_now_add
            }
        )
