from django.db import migrations
from django.contrib.auth.hashers import make_password

def seed_roles_datospersonales_usuarios(apps, schema_editor):
    Rol = apps.get_model('login_app', 'Rol')
    Usuario = apps.get_model('login_app', 'Usuario')
    DatosPersonales = apps.get_model('usuarios', 'DatosPersonales')

    default_password = '0123456789'

    for rol in Rol.objects.all():
        # 1) Crear DatosPersonales Invitado con número único INV-XX
        numero = f"INV-{rol.id:02d}"
        datos, _ = DatosPersonales.objects.get_or_create(
            nombres          = 'Invitado',
            apellido_paterno = rol.nombre,
            defaults={
                'numero_empleado': numero,
                'correo': '',
                'telefono': '',
            }
        )
        # 2) Crear Usuario Invitado
        username = f"Invitado.{rol.nombre.replace(' ', '')}"
        Usuario.objects.get_or_create(
            nombre_usuario = username,
            defaults={
                'password':  make_password(default_password),
                'id_rol_id': rol.id,
                'id_dato':   datos.id,
                'estado':    True,
            }
        )

class Migration(migrations.Migration):
    dependencies = [
        ('login_app', '0001_initial'),
        ('usuarios',  '0001_initial'),
    ]
    operations = [
        migrations.RunPython(seed_roles_datospersonales_usuarios, migrations.RunPython.noop),
    ]