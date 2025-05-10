from django.db import migrations
from django.contrib.auth.hashers import make_password

def seed_roles_and_guests(apps, schema_editor):
    Rol = apps.get_model('login_app', 'Rol')
    Usuario = apps.get_model('login_app', 'Usuario')
    DatosPersonales = apps.get_model('usuarios', 'DatosPersonales')

    # 1) Roles
    roles = []
    for nombre in (
        "Super Administrador",
        "Administrador de Almacén",
        "Supervisor de Almacén",
        "Salidas de Almacén",
    ):
        rol, _ = Rol.objects.get_or_create(nombre=nombre)
        roles.append(rol)

    # 2) Usuarios invitados
    default_password = make_password('0123456789')
    for rol in roles:
        dp, _ = DatosPersonales.objects.get_or_create(
            nombres='Invitado',
            apellido_paterno=rol.nombre,
            defaults={'correo': '', 'numero_empleado': '', 'telefono': ''}
        )
        Usuario.objects.get_or_create(
            nombre_usuario=f"Invitado.{rol.nombre.replace(' ', '')}",
            defaults={
                'contraseña': default_password,
                'id_rol_id': rol.id,
                'id_dato': dp.id,
                'estado': True,
            }
        )

class Migration(migrations.Migration):
    dependencies = [
        ('login_app', '0001_initial'),
        ('usuarios', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_roles_and_guests),
    ]
