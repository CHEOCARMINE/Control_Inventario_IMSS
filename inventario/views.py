from django.db.models import F
from django.urls import reverse
from django.http import JsonResponse
from django.forms import formset_factory
from django.core.paginator import Paginator
from django.db import transaction, IntegrityError
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from .models import Tipo, Producto, Entrada, EntradaLinea
from django.shortcuts import render, get_object_or_404, redirect
from base.models import Modulo, Accion, ReferenciasLog, LogsSistema
from auxiliares_inventario.models import Catalogo, Subcatalogo, Marca
from login_app.decorators import login_required, supervisor_required, almacen_required
from .forms import (TipoForm, ProductoForm, EntradaForm, EntradaLineaFormSetRegistro, EntradaLineaFormSetEdicion)

# Helper para registrar logs 
def _registrar_log(request, tabla, id_registro, nombre_modulo, nombre_accion):
    try:
        user_id_dato = getattr(request.user, 'id_dato', None) or request.user.pk
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

# Tipo

# LISTADO
@login_required
@almacen_required
def lista_tipo(request):
    nombre          = request.GET.get('nombre', '').strip()
    categoria_id    = request.GET.get('categoria', '').strip()
    subcategoria_id = request.GET.get('subcategoria', '').strip()
    estado          = request.GET.get('estado', '').strip()

    qs = Tipo.objects.select_related('Subcatalogo__catalogo', 'unidad_medida').all()

    if nombre:
        qs = qs.filter(nombre__icontains=nombre)
    if categoria_id.isdigit():
        qs = qs.filter(Subcatalogo__catalogo_id=int(categoria_id))
    if subcategoria_id.isdigit():
        qs = qs.filter(Subcatalogo_id=int(subcategoria_id))
    if estado in ['activo', 'inactivo']:
        qs = qs.filter(estado=(estado == 'activo'))

    qs = qs.order_by('nombre')
    page_obj = Paginator(qs, 10).get_page(request.GET.get('page'))

    catalogos = Catalogo.objects.filter(estado=True).order_by('nombre')
    if categoria_id.isdigit():
        subcatalogos = Subcatalogo.objects.filter(
            catalogo_id=int(categoria_id), estado=True
        ).order_by('nombre')
    else:
        subcatalogos = Subcatalogo.objects.filter(estado=True).order_by('nombre')

    mensaje_exito = request.session.pop('tipo_success', None)
    mensaje_error = request.session.pop('tipo_error', None)

    return render(request, 'inventario/tipos.html', {
        'page_obj':       page_obj,
        'filter': {
            'nombre':       nombre,
            'categoria':    categoria_id,
            'subcategoria': subcategoria_id,
            'estado':       estado,
        },
        'catalogos':      catalogos,
        'subcatalogos':   subcatalogos,
        'mensaje_exito':  mensaje_exito,
        'mensaje_error':  mensaje_error,
    })

# AGREGAR
@login_required
@almacen_required
def agregar_tipo(request):
    if request.method == 'POST':
        form = TipoForm(request.POST, crear=True)
        if form.is_valid():
            t = form.save(commit=False)
            t.estado = True
            t.save()
            _registrar_log(
                request,
                tabla         = "tipo",
                id_registro   = t.id,
                nombre_modulo = "Inventario",
                nombre_accion = "Crear"
            )
            request.session['tipo_success'] = 'Tipo creada correctamente.'
            return JsonResponse({
                'success':      True,
                'redirect_url': reverse('inventario:lista_tipos')
            })
        else:
            html_form = render_to_string(
                'inventario/modales/fragmento_form_tipo.html',
                {'form': form, 'crear': True},
                request=request
            )
            return JsonResponse({'success': False, 'html_form': html_form})
    else:
        form = TipoForm(crear=True)
        return render(request,
                        'inventario/modales/modal_agregar_tipo.html',
                        {'form': form, 'crear': True})

# EDITAR
@login_required
@almacen_required
def editar_tipo(request, pk):
    t = get_object_or_404(Tipo, pk=pk)
    if request.method == 'POST':
        form = TipoForm(request.POST, instance=t)
        if form.is_valid():
            form.save()
            _registrar_log(
                request,
                tabla         = "tipo",
                id_registro   = t.id,
                nombre_modulo = "Inventario",
                nombre_accion = "Editar"
            )
            request.session['tipo_success'] = 'Tipo actualizada correctamente.'
            return JsonResponse({
                'success':      True,
                'redirect_url': reverse('inventario:lista_tipos')
            })
        else:
            html_form = render_to_string(
                'inventario/modales/fragmento_form_tipo.html',
                {'form': form, 'tipo': t},
                request=request
            )
            return JsonResponse({'success': False, 'html_form': html_form})
    else:
        form = TipoForm(instance=t)
        return render(request,
                        'inventario/modales/modal_editar_tipo.html',
                        {'form': form, 'tipo': t})

# INHABILITAR
@login_required
@almacen_required
@require_POST
def inhabilitar_tipo(request, pk):
    t = get_object_or_404(Tipo, pk=pk)
    t.estado = False
    t.save(update_fields=['estado'])
    _registrar_log(
        request,
        tabla         = "tipo",
        id_registro   = t.id,
        nombre_modulo = "Inventario",
        nombre_accion = "Inhabilitar"
    )
    request.session['tipo_success'] = 'Tipo inhabilitada correctamente.'
    return JsonResponse({
        'success':      True,
        'redirect_url': reverse('inventario:lista_tipos')
    })
# FIN DE TIPO

# INVENTARIO

# LISTADO
@login_required
@supervisor_required
def lista_productos(request):
    nombre          = request.GET.get('nombre', '').strip()
    categoria_id    = request.GET.get('categoria', '').strip()
    subcategoria_id = request.GET.get('subcategoria', '').strip()
    tipo_id     = request.GET.get('tipo', '').strip()
    estado          = request.GET.get('estado', '').strip()

    qs = Producto.objects.select_related(
        'tipo__Subcatalogo__catalogo',
        'marca'
    ).all()

    if nombre:
        qs = qs.filter(nombre__icontains=nombre)
    if tipo_id.isdigit():
        qs = qs.filter(tipo_id=int(tipo_id))
    if estado in ['activo', 'inactivo']:
        qs = qs.filter(estado=(estado == 'activo'))

    if categoria_id.isdigit():
        qs = qs.filter(tipo__Subcatalogo__catalogo_id=int(categoria_id))
    if subcategoria_id.isdigit():
        qs = qs.filter(tipo__Subcatalogo_id=int(subcategoria_id))

    qs = qs.order_by(
        'tipo__Subcatalogo__catalogo__nombre',
        'tipo__Subcatalogo__nombre',
        'tipo__nombre',
        'nombre'
    )

    page_obj = Paginator(qs, 10).get_page(request.GET.get('page'))

    catalogos = Catalogo.objects.filter(estado=True).order_by('nombre')

    if categoria_id.isdigit():
        subcatalogos = Subcatalogo.objects.filter(
            catalogo_id=int(categoria_id),
            estado=True
        ).order_by('nombre')
    else:
        subcatalogos = Subcatalogo.objects.filter(estado=True).order_by('nombre')

    tipo_qs = Tipo.objects.filter(estado=True).select_related(
        'Subcatalogo__catalogo'
    )
    if subcategoria_id.isdigit():
        tipo_qs = tipo_qs.filter(Subcatalogo_id=int(subcategoria_id))
    elif categoria_id.isdigit():
        tipo_qs = tipo_qs.filter(Subcatalogo__catalogo_id=int(categoria_id))
    tipo = tipo_qs.order_by(
        'Subcatalogo__catalogo__nombre',
        'Subcatalogo__nombre',
        'nombre'
    )

    mensaje_exito = request.session.pop('producto_success', None)
    mensaje_error = request.session.pop('producto_error', None)

    return render(request, 'inventario/productos.html', {
        'page_obj':      page_obj,
        'filter': {
            'nombre':       nombre,
            'categoria':    categoria_id,
            'subcategoria': subcategoria_id,
            'tipo':     tipo_id,
            'estado':       estado,
        },
        'catalogos':     catalogos,
        'subcatalogos':  subcatalogos,
        'tipos':     tipo,
        'mensaje_exito': mensaje_exito,
        'mensaje_error': mensaje_error,
    })

# CREAR
def crear_producto(request):
    if request.method == "POST":
        form = ProductoForm(request.POST, crear=True)
        marcas = form.marcas_list
        if form.is_valid():
            producto = form.save(commit=False)
            producto.estado = True
            producto.stock  = 0
            producto.save()
            _registrar_log(
                request,
                tabla="producto",
                id_registro=producto.id,
                nombre_modulo="Inventario",
                nombre_accion="Crear"
            )
            return JsonResponse({
                "success":        True,
                "producto_id":    producto.id,
                "producto_label": producto.nombre,
                "producto_marca": producto.marca.nombre,
                "producto_color": producto.color,
                "producto_modelo": producto.modelo,
                "producto_serie": producto.numero_serie or ""
            })
        else:
            # Renderizamos el modal completo con errores
            html = render_to_string(
                'inventario/modales/modal_crear_producto.html',
                {
                    'form': form,
                    'marcas_existentes': marcas,
                },
                request=request
            )
            return JsonResponse({'success': False, 'html_form': html})

    # GET inicial: abrimos modal en blanco para crear
    form = ProductoForm(crear=True)
    return render(
        request,
        'inventario/modales/modal_crear_producto.html',
        {
            'form': form,
            'marcas_existentes': form.marcas_list,
        }
    )

# EDITAR
@login_required
@supervisor_required
def editar_producto(request, pk):
    prod = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=prod)
        if form.is_valid():
            form.save()
            _registrar_log(
                request,
                tabla="producto",
                id_registro=prod.id,
                nombre_modulo="Inventario",
                nombre_accion="Editar"
            )
            request.session['producto_success'] = 'Producto actualizado correctamente.'
            return JsonResponse({
                'success': True,
                'redirect_url': reverse('inventario:lista_productos')
            })
        else:
            # Renderizamos el modal completo con errores
            html = render_to_string(
                'inventario/modales/modal_editar_producto.html',
                {
                    'form': form,
                    'producto': prod,
                    'marcas_existentes': form.marcas_list,
                },
                request=request
            )
            return JsonResponse({'success': False, 'html_form': html})

    # GET inicial: abrimos modal con formulario precargado
    form = ProductoForm(instance=prod)
    return render(
        request,
        'inventario/modales/modal_editar_producto.html',
        {
            'form': form,
            'producto': prod,
            'marcas_existentes': form.marcas_list,
        }
    )
# FINDE INVENTARIO

# ENTRADAS

# LISTA
@login_required
@supervisor_required 
def lista_entradas(request):
    folio       = request.GET.get('folio', '').strip()
    fecha_rec   = request.GET.get('fecha_rec', '').strip()
    producto_id = request.GET.get('producto', '').strip()
    categoria_id     = request.GET.get('categoria', '').strip()
    subcategoria_id  = request.GET.get('subcategoria', '').strip()
    tipo_id          = request.GET.get('tipo', '').strip()

    # Pre–cargamos las entradas con sus líneas y productos
    qs = Entrada.objects.prefetch_related('lineas__producto')

    # Filtros
    if folio:
        qs = qs.filter(folio__icontains=folio)
    if fecha_rec:
        qs = qs.filter(fecha_recepcion=fecha_rec)
    if producto_id.isdigit():
        qs = qs.filter(lineas__producto_id=int(producto_id))
    if categoria_id.isdigit():
        qs = qs.filter(lineas__producto__tipo__Subcatalogo__catalogo_id=int(categoria_id))
    if subcategoria_id.isdigit():
        qs = qs.filter(lineas__producto__tipo__Subcatalogo_id=int(subcategoria_id))
    if tipo_id.isdigit():
        qs = qs.filter(lineas__producto__tipo_id=int(tipo_id))

    # Ordenar y quitar duplicados por join
    qs = qs.order_by('-fecha_recepcion').distinct()

    # Para poblar los selects dependientes
    catalogos = Catalogo.objects.filter(estado=True).order_by('nombre')
    if categoria_id.isdigit():
        subcatalogos = Subcatalogo.objects.filter(
            catalogo_id=int(categoria_id), estado=True
        ).order_by('nombre')
    else:
        subcatalogos = Subcatalogo.objects.filter(estado=True).order_by('nombre')

    tipos_qs = Tipo.objects.filter(estado=True).select_related(
        'Subcatalogo__catalogo'
    )
    if subcategoria_id.isdigit():
        tipos_qs = tipos_qs.filter(Subcatalogo_id=int(subcategoria_id))
    elif categoria_id.isdigit():
        tipos_qs = tipos_qs.filter(Subcatalogo__catalogo_id=int(categoria_id))
    tipos = tipos_qs.order_by(
        'Subcatalogo__catalogo__nombre',
        'Subcatalogo__nombre',
        'nombre'
    )

    page_obj = Paginator(qs, 10).get_page(request.GET.get('page'))
    productos = Producto.objects.filter(estado=True).order_by('nombre')

    # Sacar mensajes de sesión
    mensaje_exito = request.session.pop('entrada_success', None)
    mensaje_error = request.session.pop('entrada_error', None)

    return render(request, 'inventario/entradas.html', {
        'page_obj':         page_obj,
        'filter': {
            'folio':        folio,
            'fecha_rec':    fecha_rec,
            'producto':     producto_id,
            'categoria':    categoria_id,
            'subcategoria': subcategoria_id,
            'tipo':         tipo_id,
        },
        'productos':     productos,
        'catalogos':     catalogos,
        'subcatalogos':  subcatalogos,
        'tipos':         tipos,
        'mensaje_exito': mensaje_exito,
        'mensaje_error': mensaje_error,
    })

# REGISTRAR
@login_required
@supervisor_required
def registrar_entrada(request):
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
    if request.method == 'GET':
        if not is_ajax:
            return redirect('inventario:lista_entradas')
        form_entrada   = EntradaForm()
        formset_lineas = EntradaLineaFormSetRegistro()
        todos_productos = Producto.objects.filter(estado=True).order_by(
            'tipo__Subcatalogo__catalogo__nombre',
            'tipo__Subcatalogo__nombre',
            'tipo__nombre',
            'nombre'
        )
        return render(
            request,
            'inventario/modales/modal_registrar_entrada.html',
            {
                'form_entrada':   form_entrada,
                'formset_lineas': formset_lineas,
                'todos_productos': todos_productos
            }
        )

    # POST
    form_entrada   = EntradaForm(request.POST)
    formset_lineas = EntradaLineaFormSetRegistro(request.POST)
    if form_entrada.is_valid() and formset_lineas.is_valid():
        # Validar que haya al menos una línea sin DELETE
        lineas_validas = [
            f for f in formset_lineas
            if f.cleaned_data and not f.cleaned_data.get('DELETE', False)
        ]
        if not lineas_validas:
            formset_lineas.non_form_errors = lambda: ['Debe agregar al menos un producto.']
        else:
            try:
                entrada = form_entrada.save()
            except IntegrityError:
                form_entrada.add_error('folio', 'Ya existe una entrada con este folio.')
            else:
                # Registrar log de creación
                _registrar_log(
                    request,
                    tabla         = "entrada",
                    id_registro   = entrada.id,
                    nombre_modulo = "Inventario",
                    nombre_accion = "Crear"
                )
                request.session['entrada_success'] = 'Entrada registrada correctamente.'

                # Guardar cada línea
                for form_linea in formset_lineas:
                    if form_linea.cleaned_data and not form_linea.cleaned_data.get('DELETE', False):
                        producto = form_linea.cleaned_data['producto']
                        cantidad = form_linea.cleaned_data['cantidad']

                        # Crear la línea de entrada
                        EntradaLinea.objects.create(
                            entrada=entrada,
                            producto=producto,
                            cantidad=cantidad
                        )

                        # Actualizar el stock
                        producto.stock += cantidad
                        producto.save()

                        # Log de stock ajustado
                        _registrar_log(
                            request,
                            tabla="producto",
                            id_registro=producto.id,
                            nombre_modulo="Inventario",
                            nombre_accion="Ajuste stock"
                        )

                return JsonResponse({
                    'success':      True,
                    'redirect_url': reverse('inventario:lista_entradas')
                })

        for form_linea in formset_lineas:
            # Intentar recuperar desde cleaned_data si está disponible
            producto = form_linea.cleaned_data.get('producto') if hasattr(form_linea, 'cleaned_data') else None

            # Si no está disponible (por errores), buscar el ID manualmente desde los datos enviados
            if not producto:
                producto_id = form_linea.data.get(f'{form_linea.prefix}-producto')
                if producto_id:
                    try:
                        producto = Producto.objects.get(id=producto_id)
                    except Producto.DoesNotExist:
                        producto = None

            # Si se recuperó un producto, inyectamos la info en los iniciales
            if producto:
                form_linea.initial['producto'] = producto
                form_linea.initial['marca'] = producto.marca.nombre
                form_linea.initial['color'] = producto.color
                form_linea.initial['modelo'] = producto.modelo
                form_linea.initial['numero_serie'] = producto.numero_serie

        # Si hay errores, recarga sólo el fragmento
        html_form = render_to_string(
            'inventario/modales/fragmento_form_entrada.html',
            {
                'form_entrada':   form_entrada,
                'formset_lineas': formset_lineas,
                'todos_productos': Producto.objects.filter(estado=True).order_by(
                    'tipo__Subcatalogo__catalogo__nombre',
                    'tipo__Subcatalogo__nombre',
                    'tipo__nombre',
                    'nombre'
                )
            },
            request=request
        )
        return JsonResponse({'success': False, 'html_form': html_form})

# EDITAR
@login_required
@supervisor_required
def editar_entrada(request, pk):
    entrada = get_object_or_404(Entrada, pk=pk)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if request.method == 'GET':
        if not is_ajax:
            return redirect('inventario:lista_entradas')
        form_entrada = EntradaForm(instance=entrada)
        lineas_qs = entrada.lineas.select_related('producto').all()
        formset_lineas = EntradaLineaFormSetEdicion(queryset=entrada.lineas.all(), prefix='form')

        todos_productos = Producto.objects.filter(estado=True).order_by(
            'tipo__Subcatalogo__catalogo__nombre',
            'tipo__Subcatalogo__nombre',
            'tipo__nombre',
            'nombre'
        )
        return render(
            request,
            'inventario/modales/modal_editar_entrada.html',
            {
                'form_entrada':   form_entrada,
                'formset_lineas': formset_lineas,
                'todos_productos': todos_productos,
                'entrada':        entrada,
            }
        )

    # POST AJAX
    form_entrada = EntradaForm(request.POST, instance=entrada)
    formset_lineas = EntradaLineaFormSetEdicion(request.POST)

    if form_entrada.is_valid() and formset_lineas.is_valid():
        # Validar que al menos una línea no esté marcada para eliminar
        lineas_validas = [
            f for f in formset_lineas
            if f.cleaned_data and not f.cleaned_data.get('DELETE', False)
        ]
        if not lineas_validas:
            formset_lineas.non_form_errors = lambda: ['Debe conservar al menos un producto en la entrada.']
        else:
            try:
                with transaction.atomic():
                    entrada = form_entrada.save()

                    cambios_stock = []
                    originales = {
                        linea.id: linea
                        for linea in entrada.lineas.select_related('producto').all()
                    }

                    nuevas_lineas = formset_lineas.save(commit=False)

                    for form_linea in formset_lineas:
                        if form_linea.cleaned_data.get('DELETE'):
                            continue

                        linea = form_linea.save(commit=False)
                        linea.entrada = entrada

                        cantidad_nueva = linea.cantidad
                        producto = linea.producto
                        linea_id = form_linea.instance.id

                        if linea_id in originales:
                            cantidad_original = originales[linea_id].cantidad
                            diferencia = cantidad_nueva - cantidad_original
                            if diferencia != 0:
                                producto.stock += diferencia
                                cambios_stock.append((producto, cantidad_original, cantidad_nueva))
                            del originales[linea_id]
                        else:
                            producto.stock += cantidad_nueva
                            cambios_stock.append((producto, 0, cantidad_nueva))

                        producto.save()
                        linea.save()

                    for linea_restante in originales.values():
                        producto = linea_restante.producto
                        producto.stock -= linea_restante.cantidad
                        producto.save()
                        cambios_stock.append((producto, linea_restante.cantidad, 0))
                        linea_restante.delete()

                    for form_linea in formset_lineas.deleted_forms:
                        if form_linea.instance and form_linea.instance.id:
                            linea = form_linea.instance
                            producto = linea.producto
                            producto.stock -= linea.cantidad
                            producto.save()
                            cambios_stock.append((producto, linea.cantidad, 0))
                            linea.delete()

                    _registrar_log(
                        request,
                        tabla="entrada",
                        id_registro=entrada.id,
                        nombre_modulo="Inventario",
                        nombre_accion="Editar"
                    )

                    for producto, antes, despues in cambios_stock:
                        if antes != despues:
                            _registrar_log(
                                request,
                                tabla="producto",
                                id_registro=producto.id,
                                nombre_modulo="Inventario",
                                nombre_accion="Ajuste stock",
                            )

                    request.session['entrada_success'] = 'Entrada actualizada correctamente.'
                    return JsonResponse({
                        'success': True,
                        'redirect_url': reverse('inventario:lista_entradas')
                    })

            except IntegrityError:
                form_entrada.add_error('folio', 'Ya existe una entrada con este folio.')

        # Si hay errores, volver a cargar el fragmento con los forms
        html_form = render_to_string(
            'inventario/modales/fragmento_form_entrada.html',
            {
                'form_entrada': form_entrada,
                'formset_lineas': formset_lineas,
                'todos_productos': Producto.objects.filter(estado=True).order_by(
                    'tipo__Subcatalogo__catalogo__nombre',
                    'tipo__Subcatalogo__nombre',
                    'tipo__nombre',
                    'nombre'
                ),
                'entrada': entrada,
            },
            request=request
        )
        return JsonResponse({'success': False, 'html_form': html_form})
# FIN DE ENTRADA