# Generated by Django 5.2 on 2025-06-26 11:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auxiliares_inventario', '0002_delete_proveedor'),
        ('inventario', '0010_producto_tiene_serie'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='producto',
            constraint=models.CheckConstraint(condition=models.Q(models.Q(('numero_serie__isnull', False), ('producto_padre__isnull', False)), models.Q(('numero_serie__isnull', True), ('producto_padre__isnull', True)), _connector='OR'), name='producto_parent_child_consistency'),
        ),
    ]
