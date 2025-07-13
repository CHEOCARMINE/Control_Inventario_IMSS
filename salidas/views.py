import json
from django.db.models import Q
from django.db.models import F
from django.urls import reverse
from django.utils import timezone
from .forms import ValeSalidaForm
from django.shortcuts import render
from django.http import JsonResponse
from .utils import generar_folio_automatico
from django.core.paginator import Paginator
from inventario.models import Producto, Tipo
from django.db import transaction, IntegrityError
from django.template.loader import render_to_string
from django.shortcuts import redirect, get_object_or_404
from .models import ValeSalida, ValeDetalle, Producto
from auxiliares_inventario.models import Catalogo, Subcatalogo
from solicitantes.models import Unidad, Departamento, Solicitante
from login_app.decorators import login_required, salidas_required
from base.models import Modulo, Accion, ReferenciasLog, LogsSistema

# Helper para registros de log, idéntico al de inventario
def _registrar_log(request, tabla, id_registro, nombre_modulo, nombre_accion):
    user_id_dato = getattr(request.user, 'id_dato', None) or request.user.pk
    if not user_id_dato:
        return
    try:
        with transaction.atomic():
            ref = ReferenciasLog.objects.create(tabla=tabla, id_registro=id_registro)
            modulo = Modulo.objects.get(nombre=nombre_modulo)
            accion = Accion.objects.get(nombre=nombre_accion)
            LogsSistema.objects.create(
                id_dato    = user_id_dato,
                id_modulo  = modulo,
                id_accion  = accion,
                id_ref_log = ref,
                ip_origen  = request.META.get('REMOTE_ADDR')
            )
    except Exception:
        pass

# Vista para listar productos disponibles para salida
@login_required
@salidas_required
def productos_para_salida(request):
    mensaje_exito = request.session.pop('salida_success', None)
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
        'mensaje_exito': mensaje_exito,
    })

# Registrar Salida
@login_required
@salidas_required
def registrar_salida(request):
    # GET: devolver modal con el form
    if request.method == 'GET':
        solicitantes  = Solicitante.objects.select_related('unidad','departamento').filter(estado=True)
        unidades      = Unidad.objects.filter(estado=True)
        departamentos = Departamento.objects.filter(estado=True)

        datos_solicitantes = {
            s.id: {'unidad_id': s.unidad_id, 'departamento_id': s.departamento_id}
            for s in solicitantes
        }
        datos_unidades = {}
        for d in departamentos:
            for u in d.unidades.all():
                datos_unidades.setdefault(u.id, []).append({'id': d.id, 'nombre': d.nombre})

        todos_solicitantes = [
            {'id': s.id, 'nombre': s.nombre,
                'unidad_id': s.unidad_id, 'departamento_id': s.departamento_id}
            for s in solicitantes
        ]
        todos_unidades = [
            {'id': u.id, 'nombre': u.nombre,
                'departamentos': [d.id for d in u.departamentos.all()]}
            for u in unidades
        ]

        departamentos_list = [
            {'id': d.id, 'nombre': d.nombre}
            for d in departamentos
        ]

        return render(request,
                        'salidas/modales/modal_registrar_salida.html',
                        {
                            'solicitantes': solicitantes,
                            'unidades': unidades,
                            'departamentos': departamentos,
                            'datos_solicitantes_json': json.dumps(datos_solicitantes),
                            'datos_unidades_json':      json.dumps(datos_unidades),
                            'todos_solicitantes_json':  json.dumps(todos_solicitantes),
                            'todos_unidades_json':      json.dumps(todos_unidades),
                            'departamentos_list_json':  json.dumps(departamentos_list),
                        }
        )

    # POST AJAX: procesar guardado de la salida
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
    if request.method == 'POST' and is_ajax:
        form = ValeSalidaForm(request.POST)
        if form.is_valid():
            carrito      = form.cleaned_data['carrito_json']
            solicitante  = form.cleaned_data['solicitante']
            unidad       = form.cleaned_data['unidad']
            departamento = form.cleaned_data['departamento']

            try:
                with transaction.atomic():
                    # Crear cabecera de vale
                    folio = generar_folio_automatico()
                    vale = ValeSalida.objects.create(
                        folio          = folio,
                        solicitante    = solicitante,
                        unidad         = unidad,
                        departamento   = departamento,
                        fecha_creacion = timezone.now()
                    )
                    _registrar_log(request, "vale_salida", vale.id, "Salidas", "Crear")

                    # Procesar cada ítem del carrito
                    for item in carrito:
                        prod = get_object_or_404(Producto, pk=item['id'])

                        if item.get('esHijo'):
                            ValeDetalle.objects.create(vale=vale, producto=prod, cantidad=1)

                            prod.stock = F('stock') - 1
                            prod.save(update_fields=['stock'])
                            prod.refresh_from_db(fields=['stock'])
                            _registrar_log(request, "producto", prod.id, "Salidas", "Ajuste stock")

                            prod.estado = False
                            prod.save(update_fields=['estado'])
                            _registrar_log(request, "producto", prod.id, "Salidas", "Desactivar hijo")

                            padre = prod.producto_padre
                            padre.stock = F('stock') - 1
                            padre.save(update_fields=['stock'])
                            padre.refresh_from_db(fields=['stock'])
                            _registrar_log(request, "producto", padre.id, "Salidas", "Ajuste stock")
                        else:
                            cantidad = item['cantidad']
                            ValeDetalle.objects.create(vale=vale, producto=prod, cantidad=cantidad)

                            prod.stock = F('stock') - cantidad
                            prod.save(update_fields=['stock'])
                            prod.refresh_from_db(fields=['stock'])
                            _registrar_log(request, "producto", prod.id, "Salidas", "Ajuste stock")

                    # Guardar mensaje en sesión y redirigir
                    request.session['salida_success'] = f"Salida registrada correctamente. Folio: {folio}"
                    return JsonResponse({
                        'success':      True,
                        'redirect_url': reverse('salidas:productos_para_salida')
                    })
            except IntegrityError:
                form.add_error(None, "Error al guardar la salida. Intenta de nuevo.")

        # Si hay errores de validación, recargamos solo el fragmento del form
        html = render_to_string(
            'salidas/modales/fragmento_form_salida.html',
            {
                'form': form,
                'solicitantes':  Solicitante.objects.filter(estado=True),
                'unidades':      Unidad.objects.filter(estado=True),
                'departamentos': Departamento.objects.filter(estado=True),
            },
            request=request
        )
        return JsonResponse({'success': False, 'html_form': html})

    # cualquier otro caso, redirigir
    return redirect('salidas:productos_para_salida')

# Lista de salidas registradas
@login_required
@salidas_required
def lista_salidas(request):
    # Filtros
    folio        = request.GET.get('folio', '').strip()
    solicitante  = request.GET.get('solicitante', '').strip()
    unidad       = request.GET.get('unidad', '').strip()
    departamento = request.GET.get('departamento', '').strip()
    producto     = request.GET.get('producto', '').strip()
    estado       = request.GET.get('estado', '').strip()

    # Query optimizada
    qs = ValeSalida.objects.select_related(
                'solicitante', 'unidad', 'departamento'
            ).prefetch_related('detalles__producto')

    # Aplicar filtros simples
    if folio:
        qs = qs.filter(folio__icontains=folio)
    if solicitante.isdigit():
        qs = qs.filter(solicitante_id=int(solicitante))
    if unidad.isdigit():
        qs = qs.filter(unidad_id=int(unidad))
    if departamento.isdigit():
        qs = qs.filter(departamento_id=int(departamento))
    if producto.isdigit():
        prod_id = int(producto)
        qs = qs.filter(Q(detalles__producto_id=prod_id)| Q(detalles__producto__producto_padre_id=prod_id))
    if estado:
        qs = qs.filter(estado=estado)

    # Ordenar y paginar
    qs = qs.order_by('-fecha_creacion').distinct()
    page_obj = Paginator(qs, 10).get_page(request.GET.get('page'))

    # Datos para selects
    context = {
        'page_obj':     page_obj,
        'filter': {
            'folio':        folio,
            'solicitante':  solicitante,
            'unidad':       unidad,
            'departamento': departamento,
            'producto':     producto,
            'estado':       estado,
        },
        'solicitantes':  Solicitante.objects.order_by('nombre'),
        'unidades':       Unidad.objects.order_by('nombre'),
        'departamentos':  Departamento.objects.order_by('nombre'),
        'productos':      Producto.objects.filter(
                                producto_padre__isnull=True
                            ).order_by('nombre'),
    }
    return render(request, 'salidas/lista_salidas.html', context)