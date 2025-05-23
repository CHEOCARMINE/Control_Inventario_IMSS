from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.db import connection

@receiver(post_migrate)
def insertar_cargos_basicos(sender, **kwargs):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name='solicitantes_cargo';"
        )
        tabla_existe = cursor.fetchone()

    if tabla_existe:
        from .models import Cargo
        if not Cargo.objects.exists():
            for nombre in ['Coordinador', 'Director', 'Administrador']:
                Cargo.objects.create(nombre=nombre)
