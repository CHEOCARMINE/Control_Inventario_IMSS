from django.urls import reverse
from django.db.models import F, Q
from django.http import JsonResponse
from django.forms import formset_factory
from django.core.paginator import Paginator
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
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
@login_required
@supervisor_required
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
                "success":         True,
                "producto_id":     producto.id,
                "producto_label":  producto.nombre,
                "producto_marca":  producto.marca.nombre,
                "producto_color":  producto.color,
                "producto_modelo": producto.modelo,
                "producto_serie":  producto.numero_serie or "",
                "producto_tiene_serie":     producto.tiene_serie,
            })
        else:
            html = render_to_string(
                'inventario/modales/modal_crear_producto.html',
                {
                    'form': form,
                    'marcas_existentes': marcas,
                },
                request=request
            )
            return JsonResponse({'success': False, 'html_form': html})

    # GET inicial: creamos el form en 'crear' mode
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
        form = ProductoForm(request.POST, crear=False, instance=prod)
        marcas = form.marcas_list

        if form.is_valid():
            producto = form.save()

            if producto.producto_padre is None:
                producto.productos_hijos.update(
                    tipo=producto.tipo,
                    nombre=producto.nombre,
                    modelo=producto.modelo,
                    marca=producto.marca,
                    color=producto.color,
                    descripcion=producto.descripcion,
                    costo_unitario=producto.costo_unitario
                )

            _registrar_log(
                request,
                tabla="producto",
                id_registro=producto.id,
                nombre_modulo="Inventario",
                nombre_accion="Editar"
            )
            request.session['producto_success'] = 'Producto actualizado correctamente.'
            return JsonResponse({
                'success': True,
                'redirect_url': reverse('inventario:lista_productos')
            })

        else:
            html = render_to_string(
                'inventario/modales/modal_editar_producto.html',
                {
                    'form': form,
                    'producto': prod,
                    'marcas_existentes': marcas,
                },
                request=request
            )
            return JsonResponse({'success': False, 'html_form': html})

    # GET inicial: instanciar form con los datos actuales
    form = ProductoForm(crear=False, instance=prod)
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
        formset_lineas = EntradaLineaFormSetRegistro(queryset=EntradaLinea.objects.none())
        todos_productos = Producto.objects.filter(estado=True, numero_serie__isnull=True).order_by(
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
                productos_afectados = set()

                for form_linea in formset_lineas:
                    if form_linea.cleaned_data and not form_linea.cleaned_data.get('DELETE', False):
                        producto = form_linea.cleaned_data['producto']
                        cantidad = form_linea.cleaned_data['cantidad']
                        numero_serie = form_linea.cleaned_data.get('numero_serie')

                        if numero_serie:
                            # Validación redundante por seguridad
                            if Producto.objects.filter(numero_serie=numero_serie).exists():
                                form_linea.add_error('numero_serie', 'Ya existe un producto con ese número de serie.')
                                raise ValidationError("Número de serie duplicado.")

                            # Crear producto hijo
                            producto_hijo = Producto.objects.create(
                                tipo=producto.tipo,
                                nombre=producto.nombre,
                                modelo=producto.modelo,
                                marca=producto.marca,
                                color=producto.color,
                                descripcion=producto.descripcion,
                                nota=producto.nota,
                                costo_unitario=producto.costo_unitario,
                                numero_serie=numero_serie,
                                producto_padre=producto,
                                stock=1
                            )

                            EntradaLinea.objects.create(
                                entrada=entrada,
                                producto=producto_hijo,
                                cantidad=1
                            )

                            productos_afectados.add(producto.id)

                            _registrar_log(
                                request,
                                tabla="producto",
                                id_registro=producto_hijo.id,
                                nombre_modulo="Inventario",
                                nombre_accion="Crear hijo"
                            )

                        else:
                            EntradaLinea.objects.create(
                                entrada=entrada,
                                producto=producto,
                                cantidad=cantidad
                            )

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

                # Actualizar stock de productos padres si se crearon hijos
                productos_padres_actualizados = Producto.objects.filter(id__in=productos_afectados)
                for padre in productos_padres_actualizados:
                    total_hijos = Producto.objects.filter(producto_padre=padre).count()
                    padre.stock = total_hijos
                    padre.save()

                    _registrar_log(
                        request,
                        tabla="producto",
                        id_registro=padre.id,
                        nombre_modulo="Inventario",
                        nombre_accion="Ajuste stock (por hijos)"
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
            'form_entrada': form_entrada,
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
        formset_lineas = EntradaLineaFormSetEdicion(queryset=entrada.lineas.all())
        entrada_prod_ids = list(entrada.lineas.values_list('producto_id', flat=True))

        todos_productos = Producto.objects.filter(estado=True).filter(
            Q(numero_serie__isnull=True) | Q(id__in=entrada_prod_ids)
        ).order_by(
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
    form_entrada   = EntradaForm(request.POST, instance=entrada)
    formset_lineas = EntradaLineaFormSetEdicion(request.POST, queryset=entrada.lineas.all())

    # Guardar primero la cabecera y controlar duplicados (folio)
    if form_entrada.is_valid():
        try:
            entrada.folio = form_entrada.cleaned_data['folio']
            entrada.fecha_recepcion = form_entrada.cleaned_data['fecha_recepcion']
            entrada.save(update_fields=['folio', 'fecha_recepcion'])
        except IntegrityError as e:
            if 'folio' in str(e).lower():
                form_entrada.add_error('folio', 'Ya existe una entrada con este folio.')
            else:
                raise
            html_form = render_to_string(
                'inventario/modales/fragmento_form_entrada.html',
                {
                    'form_entrada': form_entrada,
                    'formset_lineas': formset_lineas,
                    'todos_productos': Producto.objects.filter(estado=True)
                        .order_by(
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

    # Procesar líneas
    if formset_lineas.is_valid():
        # Asegurar que queda al menos una línea
        lineas_validas = [
            f for f in formset_lineas
            if f.cleaned_data and not f.cleaned_data.get('DELETE', False)
        ]
        if not lineas_validas:
            formset_lineas.non_form_errors = lambda: ['Debe conservar al menos un producto en la entrada.']
        else:
            with transaction.atomic():
                cambios_stock = []

                # Guardar originales
                originales = {
                    linea.id: linea
                    for linea in entrada.lineas.select_related('producto').all()
                }

                # Nuevas y ediciones
                for form_linea in formset_lineas:
                    if form_linea.cleaned_data.get('DELETE'):
                        continue

                    producto = form_linea.cleaned_data['producto']
                    cantidad = form_linea.cleaned_data['cantidad']
                    numero_serie = form_linea.cleaned_data.get('numero_serie')

                    if producto and not producto.numero_serie and numero_serie:
                        hijo_existente = Producto.objects.filter(numero_serie=numero_serie).first()
                        if hijo_existente:
                            producto = hijo_existente
                        else:
                            producto = Producto.objects.create(
                                tipo=producto.tipo,
                                nombre=producto.nombre,
                                modelo=producto.modelo,
                                marca=producto.marca,
                                color=producto.color,
                                descripcion=producto.descripcion,
                                nota=producto.nota,
                                costo_unitario=producto.costo_unitario,
                                numero_serie=numero_serie,
                                producto_padre=producto,
                                stock=1
                            )
                            _registrar_log(
                                request,
                                tabla="producto",
                                id_registro=producto.id,
                                nombre_modulo="Inventario",
                                nombre_accion="Crear hijo"
                            )

                    linea = form_linea.save(commit=False)
                    linea.producto = producto
                    linea.entrada = entrada

                    cantidad_nueva = linea.cantidad
                    linea_id = form_linea.instance.id

                    if linea_id in originales:
                        # Cambio de cantidad en línea existente
                        cantidad_original = originales[linea_id].cantidad
                        diff = cantidad_nueva - cantidad_original
                        if diff:
                            producto.stock += diff
                            cambios_stock.append((producto, cantidad_original, cantidad_nueva))
                        del originales[linea_id]
                    else:
                        # Línea nueva
                        producto.stock += cantidad_nueva
                        cambios_stock.append((producto, 0, cantidad_nueva))

                    producto.save()
                    linea.save()

                # Eliminación de las originales faltantes
                for linea_rest in originales.values():
                    prod = linea_rest.producto
                    if prod.numero_serie:
                        # Producto hijo: primero borramos la línea...
                        padre = prod.producto_padre
                        stock_antes = padre.stock
                        linea_rest.delete()
                        # ...luego borramos el hijo
                        prod.delete()
                        # finalmente decrementamos 1 al padre
                        padre.stock = F('stock') - 1
                        padre.save()
                        padre.refresh_from_db(fields=['stock'])
                        cambios_stock.append((padre, stock_antes, padre.stock))
                    else:
                        # Producto normal
                        antes = prod.stock
                        prod.stock = F('stock') - linea_rest.cantidad
                        prod.save()
                        prod.refresh_from_db(fields=['stock'])
                        cambios_stock.append((prod, antes, prod.stock))
                        linea_rest.delete()

                # Eliminación de las líneas marcadas DELETE
                for form_linea in formset_lineas.deleted_forms:
                    linea = form_linea.instance
                    prod = linea.producto
                    if prod.numero_serie:
                        padre = prod.producto_padre
                        stock_antes = padre.stock
                        linea.delete()
                        prod.delete()
                        padre.stock = F('stock') - 1
                        padre.save()
                        padre.refresh_from_db(fields=['stock'])
                        cambios_stock.append((padre, stock_antes, padre.stock))
                    else:
                        antes = prod.stock
                        prod.stock = F('stock') - linea.cantidad
                        prod.save()
                        prod.refresh_from_db(fields=['stock'])
                        cambios_stock.append((prod, antes, prod.stock))
                        linea.delete()

                # Logs
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
                            nombre_accion="Ajuste stock"
                        )

                request.session['entrada_success'] = 'Entrada actualizada correctamente.'
                return JsonResponse({
                    'success': True,
                    'redirect_url': reverse('inventario:lista_entradas')
                })

    # Si hay errores, recargamos el modal
    html_form = render_to_string(
        'inventario/modales/fragmento_form_entrada.html',
        {
            'form_entrada': form_entrada,
            'formset_lineas': formset_lineas,
            'todos_productos': Producto.objects.filter(estado=True)
                .order_by(
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