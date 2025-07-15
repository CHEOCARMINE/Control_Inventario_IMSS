import os
from django.conf import settings
from django.contrib.staticfiles import finders

def link_callback(uri, rel):
    """
    Convierte URLs de {% static %} en rutas de disco
    para que xhtml2pdf pueda abrir imágenes, CSS y tipografías.
    """
    # Sólo procesamos las rutas que empiecen con STATIC_URL
    if uri.startswith(settings.STATIC_URL):
        # quitar el prefijo /static/
        path = uri[len(settings.STATIC_URL):]
        # buscar la ruta real en disco
        real_path = finders.find(path)
        if real_path:
            return real_path
    # si no es un static o no lo encontró, devolver uri tal cual
    return uri
