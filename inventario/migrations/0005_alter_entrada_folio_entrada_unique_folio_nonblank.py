# Generated by Django 5.2 on 2025-06-12 23:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0004_rename_herencia_tipo_rename_herencia_producto_tipo'),
    ]

    operations = [
        migrations.AlterField(
            model_name='entrada',
            name='folio',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddConstraint(
            model_name='entrada',
            constraint=models.UniqueConstraint(condition=models.Q(('folio', ''), _negated=True), fields=('folio',), name='unique_folio_nonblank'),
        ),
    ]
