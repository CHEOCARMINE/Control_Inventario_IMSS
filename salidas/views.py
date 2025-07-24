import io
import json
from xhtml2pdf import pisa
from django.urls import reverse
from django.conf import settings
from django.db.models import Q, F
from django.utils import timezone
from django.shortcuts import render
from pypdf import PdfReader, PdfWriter
from .utils import generar_folio_automatico
from django.core.paginator import Paginator
from inventario.models import Producto, Tipo
from django.db import transaction, IntegrityError
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from .models import ValeSalida, ValeDetalle, Producto
from django.shortcuts import redirect, get_object_or_404
from .pdf_utils import link_callback, create_watermark_page
from auxiliares_inventario.models import Catalogo, Subcatalogo
from solicitantes.models import Unidad, Departamento, Solicitante
from login_app.decorators import login_required, salidas_required
from base.models import Modulo, Accion, ReferenciasLog, LogsSistema
from .forms import ValeSalidaForm, CancelarValeForm, ValeSalidaFormEdicion

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

    # Mensajes de éxito/error
    mensaje_exito = request.session.pop('mensaje_exito', None)
    mensaje_error = request.session.pop('mensaje_error', None)

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
        'mensaje_exito': mensaje_exito,
        'mensaje_error': mensaje_error,
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

# Entregar Vale
@login_required
@salidas_required
def entregar_vale(request, pk):
    # Solo vales pendientes pueden marcarse como entregados
    vale = get_object_or_404(ValeSalida, pk=pk, estado='pendiente')

    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Cambiamos el estado y guardamos fecha de entrega
        vale.estado = 'entregado'
        vale.fecha_entrega = timezone.now()
        vale.save(update_fields=['estado', 'fecha_entrega'])

        # Registramos en tu sistema de logs
        _registrar_log(request, "vale_salida", vale.id, "Salidas", "Entregar")

        # Mensaje de éxito en sesión
        request.session['mensaje_exito'] = f"Vale {vale.folio} marcado como entregado."

        # Devolvemos OK al front
        return JsonResponse({'success': True})

    # Si no es POST/AJAX devolvemos error
    return JsonResponse({'success': False, 'error': 'Método no permitido.'}, status=405)

# Cancelar Vale
@login_required
@salidas_required
def cancelar_vale(request, pk):
    vale = get_object_or_404(ValeSalida, pk=pk, estado='pendiente')

    # GET: cargar modal con el form para motivo
    if request.method == 'GET':
        form = CancelarValeForm()
        return render(request,
                        'salidas/modales/confirmar_cancelacion.html',
                        {'vale': vale, 'form': form})

    # POST AJAX: procesar cancelación
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        form = CancelarValeForm(request.POST)
        if not form.is_valid():
            return JsonResponse({
                'success': False,
                'error': form.errors['motivo'][0]
            })

        motivo = form.cleaned_data['motivo']
        try:
            with transaction.atomic():
                # Cambiar estado y guardar motivo
                vale.estado = 'cancelado'
                vale.motivo_cancelacion = motivo
                vale.save(update_fields=['estado', 'motivo_cancelacion'])

                # Restaurar stock invirtiendo registrar_salida
                for detalle in vale.detalles.all():
                    prod = detalle.producto

                    if prod.producto_padre_id:
                        # Era hijo: reactivar y sumar 1
                        prod.estado = True
                        prod.stock = F('stock') + 1
                        prod.save(update_fields=['estado', 'stock'])
                        prod.refresh_from_db(fields=['stock'])
                        _registrar_log(request, "producto", prod.id, "Salidas", "Reactivar hijo")

                        # Sumar 1 al padre
                        padre = prod.producto_padre
                        padre.stock = F('stock') + 1
                        padre.save(update_fields=['stock'])
                        padre.refresh_from_db(fields=['stock'])
                        _registrar_log(request, "producto", padre.id, "Salidas", "Restaurar stock padre")
                    else:
                        # Producto normal: sumar la cantidad original
                        prod.stock = F('stock') + detalle.cantidad
                        prod.save(update_fields=['stock'])
                        prod.refresh_from_db(fields=['stock'])
                        _registrar_log(request, "producto", prod.id, "Salidas", "Restaurar stock normal")

                # Registrar en logs la cancelación del vale
                _registrar_log(request, "vale_salida", vale.id, "Salidas", "Cancelar")

                # Mensaje de éxito para la lista
                request.session['mensaje_exito'] = (
                    f"Vale {vale.folio} cancelado correctamente."
                )
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

        return JsonResponse({'success': True})

    # Método no permitido
    return JsonResponse(
        {'success': False, 'error': 'Método no permitido.'},
        status=405
    )

# Imprimir Vale como PDF
@login_required
@salidas_required
def imprimir_vale(request, pk):
    # Carga tu objeto
    vale = get_object_or_404(
        ValeSalida.objects
            .select_related('solicitante','unidad','departamento')
            .prefetch_related('detalles__producto'),
        pk=pk
    )

    # Render HTML → PDF en memoria
    html = render_to_string('salidas/vale_pdf.html', {'vale': vale})
    buffer_pdf = io.BytesIO()
    status = pisa.CreatePDF(html, dest=buffer_pdf, link_callback=link_callback)
    if status.err:
        return HttpResponse('Error al generar PDF', status=500)

    # Si está PENDIENTE, retorna el PDF “crudo”
    if vale.estado == 'pendiente':
        buffer_pdf.seek(0)
        response = HttpResponse(buffer_pdf.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="vale_{vale.folio}.pdf"'
        return response

    # Caso ENTREGADO/CANCELADO: estampa la marca
    buffer_pdf.seek(0)
    original = PdfReader(buffer_pdf)
    writer = PdfWriter()

    svg_file = (
        'salidas/img/watermark_entregado.svg'
        if vale.estado == 'entregado'
        else 'salidas/img/watermark_cancelado.svg'
    )
    watermark = create_watermark_page(svg_file)

    for page in original.pages:
        page.merge_page(watermark)
        writer.add_page(page)

    # Escribe y retorna el PDF final
    out_buf = io.BytesIO()
    writer.write(out_buf)
    out_buf.seek(0)
    response = HttpResponse(out_buf.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="vale_{vale.folio}.pdf"'
    return response

# Edicion de Vale
@login_required
@salidas_required
def editar_salida(request, pk):
    vale = get_object_or_404(
        ValeSalida.objects.select_related(
            'solicitante', 'unidad', 'departamento'
        ).prefetch_related('detalles__producto'),
        pk=pk
    )

    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if request.method == 'GET' and is_ajax:
        # Cargar datos para Select2
        solicitantes  = Solicitante.objects.select_related('unidad','departamento').filter(estado=True)
        unidades      = Unidad.objects.filter(estado=True)
        departamentos = Departamento.objects.filter(estado=True)
        productos_usados_ids = vale.detalles.values_list('producto_id', flat=True)

        productos_disponibles = Producto.objects.filter(
            (
                Q(estado=True, stock__gt=0) & (
                    Q(producto_padre__isnull=True) |  
                    Q(producto_padre__isnull=False, stock=1)  
                )
            ) | Q(id__in=productos_usados_ids)
        ).select_related('marca', 'tipo').order_by(
            'tipo__Subcatalogo__catalogo__nombre',
            'tipo__Subcatalogo__nombre',
            'tipo__nombre',
            'nombre'
        )

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
        departamentos_list = [{'id': d.id, 'nombre': d.nombre} for d in departamentos]

        productos_json = []
        for p in productos_disponibles:
            productos_json.append({
                'id': p.id,
                'nombre': str(p),
                'marca': {'nombre': p.marca.nombre if p.marca else ''},
                'modelo': p.modelo or '',
                'color': p.color or '',
                'numero_serie': p.numero_serie,
                'stock': p.stock,
                'tiene_serie': p.tiene_serie,
                'tiene_hijos': p.productos_hijos.exists(),
                'padre_id': p.producto_padre_id,
                'estado': 'activo' if p.estado else 'inactivo',
                'esHijo': p.producto_padre_id is not None,
                'tipo': {'nombre': p.tipo.nombre if p.tipo else ''}
            })

        detalles = vale.detalles.select_related('producto', 'producto__marca').all()
        return render(request, 'salidas/modales/modal_editar_salida.html', {
            'vale': vale,
            'solicitantes': solicitantes,
            'unidades': unidades,
            'departamentos': departamentos,
            'datos_solicitantes_json': json.dumps(datos_solicitantes),
            'datos_unidades_json':      json.dumps(datos_unidades),
            'todos_solicitantes_json':  json.dumps(todos_solicitantes),
            'todos_unidades_json':      json.dumps(todos_unidades),
            'departamentos_list_json':  json.dumps(departamentos_list),
            'productos_json': json.dumps(productos_json),
            'solo_vista': vale.estado != 'pendiente',
            'motivo_cancelacion': vale.motivo_cancelacion if vale.estado == 'cancelado' else None,
            'detalles': detalles,
            'productos_disponibles': productos_disponibles,
        })

    # POST: procesar edición
    if request.method == 'POST' and is_ajax and vale.estado == 'pendiente':
        form = ValeSalidaFormEdicion(request.POST, instance=vale)

        if form.is_valid():
            try:
                with transaction.atomic():
                    # Guardar encabezado
                    vale = form.save()

                    # Recuperar detalles actuales
                    originales = {
                        d.producto_id: d
                        for d in vale.detalles.select_related('producto')
                    }

                    # Procesar productos nuevos/modificados
                    productos_post = request.POST.getlist('producto_id[]')
                    cantidades_post = request.POST.getlist('cantidad[]')

                    nuevos = []
                    usados_ids = set()
                    for i, prod_id in enumerate(productos_post):
                        if not prod_id:
                            continue
                        prod_id = int(prod_id)
                        usados_ids.add(prod_id)

                        producto = Producto.objects.get(id=prod_id)
                        cantidad = int(cantidades_post[i]) if not producto.producto_padre_id else 1

                        if prod_id in originales:
                            detalle = originales.pop(prod_id)
                            if detalle.cantidad != cantidad:
                                diff = cantidad - detalle.cantidad
                                producto.stock = F('stock') - diff
                                producto.save(update_fields=['stock'])
                                _registrar_log(request, "producto", producto.id, "Salidas", "Ajuste stock")
                                detalle.cantidad = cantidad
                                detalle.save()
                        else:
                            ValeDetalle.objects.create(vale=vale, producto=producto, cantidad=cantidad)
                            producto.stock = F('stock') - cantidad
                            producto.save(update_fields=['stock'])
                            _registrar_log(request, "producto", producto.id, "Salidas", "Ajuste stock")

                            if producto.producto_padre_id:
                                producto.estado = False
                                producto.save(update_fields=['estado'])
                                _registrar_log(request, "producto", producto.id, "Salidas", "Desactivar hijo")

                                padre = producto.producto_padre
                                padre.stock = F('stock') - 1
                                padre.save(update_fields=['stock'])
                                _registrar_log(request, "producto", padre.id, "Salidas", "Ajuste stock")

                    # Productos eliminados → restaurar stock
                    for eliminado in originales.values():
                        producto = eliminado.producto
                        eliminado.delete()

                        if producto.producto_padre_id:
                            producto.estado = True
                            producto.stock = F('stock') + 1
                            producto.save(update_fields=['estado', 'stock'])
                            _registrar_log(request, "producto", producto.id, "Salidas", "Reactivar hijo")

                            padre = producto.producto_padre
                            padre.stock = F('stock') + 1
                            padre.save(update_fields=['stock'])
                            _registrar_log(request, "producto", padre.id, "Salidas", "Restaurar stock padre")
                        else:
                            producto.stock = F('stock') + eliminado.cantidad
                            producto.save(update_fields=['stock'])
                            _registrar_log(request, "producto", producto.id, "Salidas", "Restaurar stock")

                    _registrar_log(request, "vale_salida", vale.id, "Salidas", "Editar")
                    request.session['mensaje_exito'] = f"Vale {vale.folio} actualizado correctamente."

                    return JsonResponse({'success': True, 'redirect_url': reverse('salidas:productos_para_salida')})

            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})

        html = render_to_string('salidas/modales/fragmento_form_salida.html', {
            'form': form,
            'vale': vale,
        }, request=request)
        return JsonResponse({'success': False, 'html_form': html})

    return JsonResponse({'success': False, 'error': 'Método no permitido o vale no editable.'}, status=405)