from io import BytesIO
from openpyxl import Workbook
from django.utils import timezone
from django.http import HttpResponse
from login_app.decorators import login_required, supervisor_required

def _nombre_archivo():
    fecha = timezone.localdate().strftime("%Y%m%d")
    return f"inventario_{fecha}.xlsx"

@supervisor_required
@login_required
def inventario_excel(request):
    wb = Workbook()
    ws = wb.active
    ws.title = "Activos"

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    response = HttpResponse(
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="{_nombre_archivo()}"'
    return response