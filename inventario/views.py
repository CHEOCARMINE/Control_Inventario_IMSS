from django.db.models import F
from django.urls import reverse
from django.db import transaction
from django.http import JsonResponse
from django.forms import formset_factory
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from .models import Tipo, Producto, Entrada, EntradaLinea
from django.shortcuts import render, get_object_or_404, redirect
from base.models import Modulo, Accion, ReferenciasLog, LogsSistema
from login_app.decorators import login_required, supervisor_required
from auxiliares_inventario.models import Catalogo, Subcatalogo, Marca
from .forms import (TipoForm, ProductoForm, EntradaForm, EntradaLineaFormSet)

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
@supervisor_required
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
@supervisor_required
def agregar_tipo(request):
    if request.method == 'POST':
        form = TipoForm(request.POST, crear=True)
        if form.is_valid():
            h = form.save(commit=False)
            h.estado = True
            h.save()
            _registrar_log(
                request,
                tabla         = "tipo",
                id_registro   = h.id,
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
                {'form': form},
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
@supervisor_required
def editar_tipo(request, pk):
    h = get_object_or_404(Tipo, pk=pk)
    if request.method == 'POST':
        form = TipoForm(request.POST, instance=h)
        if form.is_valid():
            form.save()
            _registrar_log(
                request,
                tabla         = "tipo",
                id_registro   = h.id,
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
                {'form': form, 'tipo': h},
                request=request
            )
            return JsonResponse({'success': False, 'html_form': html_form})
    else:
        form = TipoForm(instance=h)
        return render(request,
                        'inventario/modales/modal_editar_tipo.html',
                        {'form': form, 'tipo': h})

# INHABILITAR
@login_required
@supervisor_required
@require_POST
def inhabilitar_tipo(request, pk):
    h = get_object_or_404(Tipo, pk=pk)
    h.estado = False
    h.save(update_fields=['estado'])
    _registrar_log(
        request,
        tabla         = "tipo",
        id_registro   = h.id,
        nombre_modulo = "Inventario",
        nombre_accion = "Inhabilitar"
    )
    request.session['tipo_success'] = 'Tipo inhabilitada correctamente.'
    return JsonResponse({
        'success':      True,
        'redirect_url': reverse('inventario:lista_tipos')
    })
# FIN DE tipo

# PRODUCTOS

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
        'tipo':     tipo,
        'mensaje_exito': mensaje_exito,
        'mensaje_error': mensaje_error,
    })

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
                tabla         = "producto",
                id_registro   = prod.id,
                nombre_modulo = "Inventario",
                nombre_accion = "Editar"
            )
            request.session['producto_success'] = 'Producto actualizado correctamente.'
            return JsonResponse({
                'success':      True,
                'redirect_url': reverse('inventario:lista_productos')
            })
        else:
            html = render_to_string(
                'inventario/modales/fragmento_form_producto.html',
                {'form': form},
                request=request
            )
            return JsonResponse({'success': False, 'html_form': html})
    else:
        form = ProductoForm(instance=prod)
        return render(
            request,
            'inventario/modales/modal_editar_producto.html',
            {'form': form, 'producto': prod}
        )

# CREAR
@login_required
@supervisor_required
def crear_producto(request):
    if request.method == "POST":
        form = ProductoForm(request.POST, crear=True)
        if form.is_valid():
            producto = form.save(commit=False)
            producto.estado = True
            producto.stock = 0
            producto.save()
            _registrar_log(
                request,
                tabla         = "producto",
                id_registro   = producto.id,
                nombre_modulo = "Inventario",
                nombre_accion = "Crear"
            )
            return JsonResponse({
                "success":         True,
                "producto_id":     producto.id,
                "producto_label":  producto.nombre,
                "producto_marca":  producto.marca.nombre,
                "producto_color":  producto.color,
                "producto_modelo": producto.modelo,
                "producto_serie":  producto.numero_serie or ""
            })
        else:
            html = render_to_string(
                "inventario/modales/fragmento_form_producto.html",
                {"form": form},
                request=request
            )
            return JsonResponse({"success": False, "html_form": html})
    else:
        form = ProductoForm(crear=True)
        return render(
            request,
            "inventario/modales/modal_crear_producto.html",
            {"form": form}
        )

# ENTRADAS

login_required
@supervisor_required
def registrar_entrada(request):
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
    if request.method == 'GET':
        if not is_ajax:
            return redirect('inventario:lista_productos')
        form_entrada   = EntradaForm()
        formset_lineas = EntradaLineaFormSet()
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
    form_entrada   = EntradaForm(request.POST)
    formset_lineas = EntradaLineaFormSet(request.POST)
    if form_entrada.is_valid() and formset_lineas.is_valid():
        entrada = form_entrada.save()
        for form_linea in formset_lineas:
            if form_linea.cleaned_data and not form_linea.cleaned_data.get('DELETE', False):
                producto = form_linea.cleaned_data['producto']
                cantidad = form_linea.cleaned_data['cantidad']
                EntradaLinea.objects.create(
                    entrada=entrada,
                    producto=producto,
                    cantidad=cantidad
                )
        return JsonResponse({
            'success':      True,
            'redirect_url': reverse('inventario:lista_productos')
        })
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