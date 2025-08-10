from io import BytesIO
from django.utils import timezone
from salidas.models import Producto
from django.http import HttpResponse
from login_app.decorators import login_required, supervisor_required
from .services.inventario_export import crear_libro_base, poblar_activos

TEXTO_ENCABEZADO = (
    "Servicios de Salud del Instituto Mexicano del Seguro Social para el Bienestar\n"
    "Coordinación Estatal de Campeche\n"
    "Departamento de Tecnología de la Información"
)

def _nombre_archivo():
    fecha = timezone.localdate().strftime("%Y%m%d")
    return f"inventario_{fecha}.xlsx"

@supervisor_required
@login_required
def inventario_excel(request):
    wb = crear_libro_base(TEXTO_ENCABEZADO)
    poblar_activos(wb, Producto, TEXTO_ENCABEZADO)

    bio = BytesIO()
    wb.save(bio)
    bio.seek(0)

    resp = HttpResponse(
        bio.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    resp["Content-Disposition"] = f'attachment; filename="{_nombre_archivo()}"'
    return resp
