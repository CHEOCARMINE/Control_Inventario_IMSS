from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from django.contrib.staticfiles import finders
from openpyxl.drawing.image import Image as XLImage
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side

# Columnas
COLUMNAS = [
    "ID","Nombre","Tipo de producto","Categoría","Marca","Modelo","Color",
    "Rol (Normal/Padre/Hijo)","Padre","Número de serie","Unidad",
    "Stock","Stock mínimo","Estado"
]

# Rutas a tus logos
LOGO_IZQ_STATIC = "salidas/img/logo_gob.png"
LOGO_DER_STATIC = "salidas/img/logo_imss.png"

# Estilos
THIN = Side(style="thin", color="999999")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
FILL_HEADER = PatternFill("solid", fgColor="EDEDED")

# Tamaños del encabezado
IMG_MAX_HEIGHT_PX = 110
COL_LOGO_WIDTH = 32
HEADER_ROW_HEIGHT = 30

def _insertar_imagen(ws, static_path, cell):
    path = finders.find(static_path)
    if not path:
        return
    img = XLImage(path)
    # Escalar manteniendo proporción a la altura objetivo
    try:
        ratio = IMG_MAX_HEIGHT_PX / float(img.height)
        img.height = int(IMG_MAX_HEIGHT_PX)
        img.width = int(img.width * ratio)
    except Exception:
        pass
    img.anchor = cell
    ws.add_image(img)

def _encabezado_en_hoja(ws, texto_centro, total_cols):
    # Altura generosa de las 3 filas del encabezado
    for r in (1, 2, 3):
        ws.row_dimensions[r].height = HEADER_ROW_HEIGHT

    # Reservar columnas para logos (A y última) y ensancharlas
    last_letter = get_column_letter(total_cols)
    ws.column_dimensions["A"].width = COL_LOGO_WIDTH
    ws.column_dimensions[last_letter].width = COL_LOGO_WIDTH

    # Texto centrado: C1 : (última-2)3 para no chocar con los logos
    start_col = 3  # C
    end_col = max(4, total_cols - 2)
    ws.merge_cells(start_row=1, start_column=start_col, end_row=3, end_column=end_col)
    c = ws.cell(row=1, column=start_col)
    c.value = texto_centro
    c.font = Font(bold=True, size=12)
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    # Insertar logos dentro del área del header
    _insertar_imagen(ws, LOGO_IZQ_STATIC, "A1")
    _insertar_imagen(ws, LOGO_DER_STATIC, f"{last_letter}1")

def _titulos_tabla(ws, fila_titulo=5):
    for idx, nombre in enumerate(COLUMNAS, start=1):
        cell = ws.cell(row=fila_titulo, column=idx, value=nombre)
        cell.font = Font(bold=True)
        cell.fill = FILL_HEADER
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = BORDER

    # Congelar encabezado + fila de títulos
    ws.freeze_panes = "A6"

    # AutoFilter
    last_col = get_column_letter(len(COLUMNAS))
    ws.auto_filter.ref = f"A{fila_titulo}:{last_col}{fila_titulo}"

    # Anchos sugeridos 
    widths = [8,34,18,18,16,16,12,18,22,22,10,12,12,12]
    for i, w in enumerate(widths, start=1):
        if i == 1 or i == len(COLUMNAS):
            continue
        ws.column_dimensions[get_column_letter(i)].width = w

def _crear_hoja(wb, nombre, texto_encabezado):
    ws = wb.create_sheet(title=nombre)
    _encabezado_en_hoja(ws, texto_encabezado, total_cols=len(COLUMNAS))
    _titulos_tabla(ws, fila_titulo=5)
    return ws

def crear_libro_base(texto_encabezado: str) -> Workbook:
    wb = Workbook()

    # Hoja inicial -> Activos
    ws0 = wb.active
    ws0.title = "Activos"
    _encabezado_en_hoja(ws0, texto_encabezado, total_cols=len(COLUMNAS))
    _titulos_tabla(ws0, fila_titulo=5)

    _crear_hoja(wb, "Normales", texto_encabezado)
    _crear_hoja(wb, "Padres e Hijos", texto_encabezado)
    _crear_hoja(wb, "Desactivados", texto_encabezado)

    return wb