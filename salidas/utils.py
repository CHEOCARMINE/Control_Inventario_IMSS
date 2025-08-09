from .models import ValeSalida
from django.utils import timezone

# Utility function to generate automatic folio numbers for ValeSalida
def generar_folio_automatico():
    prefix = "JSAF/DTI"
    # Año actual según zona horaria de Django
    year = timezone.now().year
    # Contar vales existentes para el año actual basándonos en la fecha de creación
    existentes = ValeSalida.objects.filter(fecha_creacion__year=year).count()
    siguiente = existentes + 1
    # Formatear el número secuencial con 4 dígitos
    seq_str = str(siguiente).zfill(4)
    return f"{prefix}/{seq_str}/{year}"
