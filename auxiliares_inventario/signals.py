from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.db import connection

@receiver(post_migrate)
def insertar_datos_base(sender, **kwargs):
    # Solo ejecutar para auxiliares_inventario
    if sender.name != 'auxiliares_inventario':
        return

    # Verificar y cargar Unidades de Medida
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='auxiliares_inventario_unidaddemedida'"
        )
        tabla_unidad_existe = cursor.fetchone()
    if tabla_unidad_existe:
        from .models import UnidadDeMedida
        if not UnidadDeMedida.objects.exists():
            unidades = [
                # Métricas
                ('Milímetro', 'mm'),
                ('Centímetro', 'cm'),
                ('Metro', 'm'),
                ('Kilómetro', 'km'),
                ('Mililitro', 'ml'),
                ('Litro', 'l'),
                ('Gramo', 'g'),
                ('Kilogramo', 'kg'),
                ('Byte', 'b'),
                ('Kilobyte', 'kb'),
                ('Megabyte', 'mb'),
                ('Gigabyte', 'gb'),
                ('Terabyte', 'tb'),
                ('Pieza', 'pz'),
                ('Unidad', 'und'),
                ('Rollo', 'rll'),
                ('Kit', 'kit'),
                ('Paquete', 'pqt'),
                ('Caja', 'cja'),
                ('Conjunto', 'cjt'),
                # Imperiales
                ('Pulgada',     'in'),
                ('Pie',         'ft'),
                ('Yarda',       'yd'),
                ('Milla',       'mi'),
                ('Onza',        'oz'),
                ('Libra',       'lb'),
                ('Pinta',       'pt'),
                ('Cuarto',      'qt'),
                ('Galón',       'gal'),
            ]
            for nombre, abreviatura in unidades:
                UnidadDeMedida.objects.create(nombre=nombre, abreviatura=abreviatura)

    # Verificar y cargar Marcas
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='auxiliares_inventario_marca'"
        )
        tabla_marca_existe = cursor.fetchone()
    if tabla_marca_existe:
        from .models import Marca
        if not Marca.objects.exists():
            marcas = [
                'HP',
                'Lenovo',
                'Dell',
                'Asus',
                'Acer',
                'Office Depot',
                'RadioShack',
                'Steren',
            ]
            for nombre in marcas:
                Marca.objects.create(nombre=nombre)

# Catálogos y Subcatálogos 
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='auxiliares_inventario_catalogo'"
        )
        if cursor.fetchone():
            from .models import Catalogo, Subcatalogo
            # Crear catálogos si no existen
            if not Catalogo.objects.exists():
                catalogos = [
                    'CONSUMIBLE',
                    'HARDWARE Y EQUIPOS',
                    'REDES Y CONECTIVIDAD',
                    'HERRAMIENTAS',
                    'EQUIPO AUDIOVISUAL',
                    'SEGURIDAD Y ENERGIA',
                ]
                for nombre in catalogos:
                    Catalogo.objects.create(nombre=nombre)
            # Crear subcatálogos si no existen
            if not Subcatalogo.objects.exists():
                sub_map = {
                    'CONSUMIBLE': [
                        'Toner y tintas',
                        'Material de limpieza y Mantenimiento',
                        'Medios de Almacenamiento desechables',
                    ],
                    'HARDWARE Y EQUIPOS': [
                        'Computacion',
                        'Almacenamiento',
                        'Perifericos',
                    ],
                    'REDES Y CONECTIVIDAD': [
                        'Cables',
                        'Accesorios de Red',
                    ],
                    'HERRAMIENTAS': [
                        'Herramientas fisicas',
                    ],
                    'EQUIPO AUDIOVISUAL': [
                        'Proyectores y Pantallas',
                        'Camaras',
                        'Adaptadores de Video',
                    ],
                    'SEGURIDAD Y ENERGIA': [
                        'Backup de Energia',
                    ],
                }
                for cat_nombre, subs in sub_map.items():
                    cat = Catalogo.objects.get(nombre=cat_nombre)
                    for sub in subs:
                        Subcatalogo.objects.create(catalogo=cat, nombre=sub)

