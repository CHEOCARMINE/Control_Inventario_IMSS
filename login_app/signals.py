from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth.hashers import make_password

from login_app.models import Rol, Usuario
from usuarios.models import DatosPersonales

@receiver(post_migrate)
def create_default_roles(sender, **kwargs):
    if sender.name != 'login_app':
        return
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
                'contraseña': make_password(default_password),
                'id_rol_id': rol.id,
                'id_dato': datos.id,
                'estado': True,
            }
        )