from django.apps import AppConfig


class AuxiliaresInventarioConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'auxiliares_inventario'

    def ready(self):
        import auxiliares_inventario.signals