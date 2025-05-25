from .models import Catalogo
from django.db.models import Q
from django.urls import reverse
from django.http import JsonResponse
from .models import Subcatalogo, Catalogo
from django.core.paginator import Paginator
from .forms import CatalogoForm, SubcatalogoForm
from django.template.loader import render_to_string
from django.shortcuts import render, get_object_or_404
from login_app.decorators import login_required, almacen_required
from base.models import Modulo, Accion, ReferenciasLog, LogsSistema


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

# Catalogo
# Lista
@login_required
@almacen_required
def lista_catalogos(request):
    nombre = request.GET.get('nombre', '')
    estado = request.GET.get('estado', '')

    qs = Catalogo.objects.all()
    if nombre:
        qs = qs.filter(nombre__icontains=nombre)
    if estado in ['activo', 'inactivo']:
        qs = qs.filter(estado=(estado == 'activo'))

    page_obj = Paginator(qs.order_by('nombre'), 10).get_page(request.GET.get('page'))

    mensaje_exito = request.session.pop('catalogo_success', None)
    mensaje_error = request.session.pop('catalogo_error', None)

    return render(request, 'auxiliares_inventario/catalogos.html', {
        'page_obj': page_obj,
        'filter': {'nombre': nombre, 'estado': estado},
        'mensaje_exito': mensaje_exito,
        'mensaje_error': mensaje_error,
    })

# Agregar 
@login_required
@almacen_required
def agregar_catalogo(request):
    if request.method == 'POST':
        form = CatalogoForm(request.POST, crear=True)
        if form.is_valid():
            cat = form.save(commit=False)
            cat.estado = True
            cat.save()
            _registrar_log(
                request,
                tabla="catalogo",
                id_registro=cat.id,
                nombre_modulo="Auxiliares",
                nombre_accion="Crear"
            )
            request.session['catalogo_success'] = 'Categoría agregada correctamente.'
            return JsonResponse({
                'success': True,
                'redirect_url': reverse('catalogo_list')
            })
        else:
            html_form = render_to_string(
                'auxiliares_inventario/modales/fragmento_form_catalogo.html',
                {'form': form},
                request=request
            )
            return JsonResponse({'success': False, 'html_form': html_form})
    else:
        form = CatalogoForm(crear=True)
        return render(request,
                        'auxiliares_inventario/modales/modal_agregar_catalogo.html',
                        {'form': form})

# Editar
@login_required
@almacen_required
def editar_catalogo(request, pk):
    """
    Vista AJAX para editar una categoría existente.
    Muestra el campo 'estado' para permitir activar/desactivar.
    """
    cat = get_object_or_404(Catalogo, pk=pk)

    if request.method == 'POST':
        form = CatalogoForm(request.POST, instance=cat)
        if form.is_valid():
            form.save()
            _registrar_log(
                request,
                tabla="catalogo",
                id_registro=cat.id,
                nombre_modulo="Auxiliares",
                nombre_accion="Editar"
            )
            request.session['catalogo_success'] = 'Categoría actualizada correctamente.'
            return JsonResponse({
                'success': True,
                'redirect_url': reverse('catalogo_list')
            })
        else:
            html_form = render_to_string(
                'auxiliares_inventario/modales/fragmento_form_catalogo.html',
                {'form': form, 'cat': cat},
                request=request
            )
            return JsonResponse({'success': False, 'html_form': html_form})
    else:
        form = CatalogoForm(instance=cat)
        return render(request,
                        'auxiliares_inventario/modales/modal_editar_catalogo.html',
                        {'form': form, 'cat': cat})
# Fin de catalogo

# Subcatalogos
# Lista 
@login_required
@almacen_required
def lista_subcatalogos(request):
    """
    Muestra el listado de Subcategorías con filtros por nombre y catálogo,
    paginación de 10 en 10 y mensajes flash.
    """
    nombre   = request.GET.get('nombre', '')
    cat_id   = request.GET.get('catalogo', '')
    qs       = Subcatalogo.objects.select_related('catalogo').all()

    if nombre:
        qs = qs.filter(nombre__icontains=nombre)
    if cat_id.isdigit():
        qs = qs.filter(catalogo_id=int(cat_id))

    page_obj       = Paginator(qs.order_by('catalogo__nombre', 'nombre'), 10) \
                        .get_page(request.GET.get('page'))
    mensaje_exito  = request.session.pop('subcatalogo_success', None)
    mensaje_error  = request.session.pop('subcatalogo_error', None)
    # Para el filtro de catálogo mostramos solo activos
    catalogos_act = Catalogo.objects.filter(estado=True).order_by('nombre')

    return render(request, 'auxiliares_inventario/subcatalogos.html', {
        'page_obj': page_obj,
        'filter':   {'nombre': nombre, 'catalogo': cat_id},
        'catalogos': catalogos_act,
        'mensaje_exito': mensaje_exito,
        'mensaje_error': mensaje_error,
    })

# Agregar
@login_required
@almacen_required
def agregar_subcatalogos(request):
    """
    Crea una nueva Subcategoría vía AJAX.
    Oculta 'estado' en el formulario y asigna estado=True.
    """
    if request.method == 'POST':
        form = SubcatalogoForm(request.POST, crear=True)
        if form.is_valid():
            sub = form.save(commit=False)
            sub.estado = True
            sub.save()
            # registrar log
            _registrar_log(
                request,
                tabla="subcatalogo",
                id_registro=sub.id,
                nombre_modulo="Auxiliares",
                nombre_accion="Crear"
            )
            request.session['subcatalogo_success'] = 'Subcategoría agregada correctamente.'
            return JsonResponse({'success': True, 'redirect_url': reverse('subcatalogo_list')})
        else:
            html_form = render_to_string(
                'auxiliares_inventario/modales/modal_agregar_subcatalogo.html',
                {'form': form},
                request=request
            )
            return JsonResponse({'success': False, 'html_form': html_form})
    else:
        form = SubcatalogoForm(crear=True)
        return render(request,
                        'auxiliares_inventario/modales/modal_agregar_subcatalogo.html',
                        {'form': form})

# Editar
@login_required
@almacen_required
def editar_subcatalogos(request, pk):
    """
    Edita una Subcategoría existente vía AJAX.
    Muestra 'estado' para permitir activar/desactivar.
    """
    sub = get_object_or_404(Subcatalogo, pk=pk)
    if request.method == 'POST':
        form = SubcatalogoForm(request.POST, instance=sub)
        if form.is_valid():
            form.save()
            # registrar log
            _registrar_log(
                request,
                tabla="subcatalogo",
                id_registro=sub.id,
                nombre_modulo="Auxiliares",
                nombre_accion="Crear"
            )
            request.session['subcatalogo_success'] = 'Subcategoría actualizada correctamente.'
            return JsonResponse({'success': True, 'redirect_url': reverse('subcatalogo_list')})
        else:
            html_form = render_to_string(
                'auxiliares_inventario/modales/modal_editar_subcatalogo.html',
                {'form': form, 'sub': sub},
                request=request
            )
            return JsonResponse({'success': False, 'html_form': html_form})
    else:
        form = SubcatalogoForm(instance=sub)
        return render(request,
                        'auxiliares_inventario/modales/modal_editar_subcatalogo.html',
                        {'form': form, 'sub': sub})
# FIn de subcatalogos