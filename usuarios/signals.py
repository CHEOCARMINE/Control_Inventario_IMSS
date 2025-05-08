from django.db.models.signals import post_migrate
from django.dispatch import receiver

from login_app.models import Rol
from usuarios.models import DatosPersonales

@receiver(post_migrate)
def create_guest_datos(sender, **kwargs):
    """
    Al migrar la app 'usuarios', crea DatosPersonales
    con nombres='Invitado' y apellido_paterno igual al nombre del rol.
    """
    if sender.name != 'usuarios':
        return

    for rol in Rol.objects.all():
        DatosPersonales.objects.get_or_create(
            nombres='Invitado',
            apellido_paterno=rol.nombre,
            defaults={
                'apellido_materno': 'Invitado',
                'correo': None,
                'numero_empleado': None,
                'telefono': None,
                # fecha_registro con auto_now_add
            }
        )