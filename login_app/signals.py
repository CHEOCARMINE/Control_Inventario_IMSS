from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth.hashers import make_password
from django.db import connection

def tabla_existe(nombre_tabla):
    """Verifica si una tabla existe en la base de datos (funciona con SQLite)."""
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=%s", [nombre_tabla]
        )
        return cursor.fetchone() is not None

@receiver(post_migrate)
def create_default_roles(sender, **kwargs):
    if sender.name != 'login_app':
        return

    if not tabla_existe('login_app_rol'):
        return

    from login_app.models import Rol

    for nombre in [
        "Super Administrador",
        "Administrador de Almacén",
        "Supervisor de Almacén",
        "Salidas de Almacén"
    ]:
        Rol.objects.get_or_create(nombre=nombre)

@receiver(post_migrate)
def create_guest_users(sender, **kwargs):
    if sender.name != 'login_app':
        return

    if not (tabla_existe('login_app_rol') and tabla_existe('login_app_usuario') and tabla_existe('usuarios_datospersonales')):
        return

    from login_app.models import Rol, Usuario
    from usuarios.models import DatosPersonales

    default_password = '0123456789'
    for rol in Rol.objects.all():
        datos = DatosPersonales.objects.filter(
            nombres='Invitado',
            apellido_paterno=rol.nombre
        ).first()
        if not datos:
            continue

        username = f"Invitado.{rol.nombre.replace(' ', '')}"
        Usuario.objects.get_or_create(
            nombre_usuario=username,
            defaults={
                'password': make_password(default_password),
                'id_rol_id': rol.id,
                'id_dato': datos.id,
                'estado': True,
            }
        )

