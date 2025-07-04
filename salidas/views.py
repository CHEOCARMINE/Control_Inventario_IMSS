from django.db.models import Q
from django.shortcuts import render
from django.core.paginator import Paginator
from inventario.models import Producto, Tipo
from auxiliares_inventario.models import Catalogo, Subcatalogo
from login_app.decorators import login_required, salidas_required


# Vista para listar productos disponibles para salida
@login_required
@salidas_required
def productos_para_salida(request):
    nombre = request.GET.get('nombre', '').strip()
    categoria_id = request.GET.get('categoria', '').strip()
    subcategoria_id = request.GET.get('subcategoria', '').strip()
    tipo_id = request.GET.get('tipo', '').strip()

    # Productos normales o hijos (activos, con stock > 0)
    qs = Producto.objects.select_related(
        'tipo__Subcatalogo__catalogo',
        'marca'
    ).filter(
        estado=True,
        stock__gt=0
    ).filter(
        Q(producto_padre__isnull=True, tiene_serie=False) |  # Productos normales
        Q(producto_padre__isnull=False)                      # Productos hijos
    )

    # Filtros
    if nombre:
        qs = qs.filter(nombre__icontains=nombre)
    if tipo_id.isdigit():
        qs = qs.filter(tipo_id=int(tipo_id))
    if subcategoria_id.isdigit():
        qs = qs.filter(tipo__Subcatalogo_id=int(subcategoria_id))
    if categoria_id.isdigit():
        qs = qs.filter(tipo__Subcatalogo__catalogo_id=int(categoria_id))

    # Ordenar por nombre
    qs = qs.order_by('tipo__nombre', 'nombre')

    # Paginación
    page_obj = Paginator(qs, 10).get_page(request.GET.get('page'))

    # Catálogos auxiliares para filtros
    catalogos = Catalogo.objects.filter(estado=True).order_by('nombre')

    if categoria_id.isdigit():
        subcatalogos = Subcatalogo.objects.filter(
            catalogo_id=int(categoria_id),
            estado=True
        ).order_by('nombre')
    else:
        subcatalogos = Subcatalogo.objects.filter(estado=True).order_by('nombre')

    tipo_qs = Tipo.objects.filter(estado=True).select_related('Subcatalogo__catalogo')
    if subcategoria_id.isdigit():
        tipo_qs = tipo_qs.filter(Subcatalogo_id=int(subcategoria_id))
    elif categoria_id.isdigit():
        tipo_qs = tipo_qs.filter(Subcatalogo__catalogo_id=int(categoria_id))
    tipos = tipo_qs.order_by(
        'Subcatalogo__catalogo__nombre',
        'Subcatalogo__nombre',
        'nombre'
    )

    return render(request, 'salidas/productos_salida.html', {
        'page_obj': page_obj,
        'filter': {
            'nombre': nombre,
            'categoria': categoria_id,
            'subcategoria': subcategoria_id,
            'tipo': tipo_id,
        },
        'catalogos': catalogos,
        'subcatalogos': subcatalogos,
        'tipos': tipos,
    })