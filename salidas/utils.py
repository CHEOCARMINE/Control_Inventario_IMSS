from django.utils import timezone
from .models import ValeSalida

# Utility function to generate automatic folio numbers for ValeSalida
def generar_folio_automatico():
    """
    Genera un folio en formato JSAF/DTI/0001/2025,
    donde el contador se reinicia cada año y se incrementa
    según los registros existentes para el año actual.
    """
    prefix = "JSAF/DTI"
    # Año actual según zona horaria de Django
    year = timezone.now().year
    # Contar vales existentes para el año actual basándonos en la fecha de creación
    existentes = ValeSalida.objects.filter(fecha_creacion__year=year).count()
    siguiente = existentes + 1
    # Formatear el número secuencial con 4 dígitos
    seq_str = str(siguiente).zfill(4)
    return f"{prefix}/{seq_str}/{year}"
