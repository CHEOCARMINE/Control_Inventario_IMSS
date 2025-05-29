from django.urls import reverse
from .models import Herencia
from django.http import JsonResponse
from .forms import HerenciaForm
from django.views.decorators.http import require_POST
from django.template.loader import render_to_string
from login_app.decorators import login_required, supervisor_required
from django.shortcuts import render, get_object_or_404, redirect
from base.models import Modulo, Accion, ReferenciasLog, LogsSistema
from django.core.paginator import Paginator
from auxiliares_inventario.models import Catalogo, Subcatalogo

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

# HERENCIA
# LISTADO
@login_required
@supervisor_required
def lista_herencias(request):
    # Capturar filtros de GET
    nombre         = request.GET.get('nombre', '').strip()
    categoria_id   = request.GET.get('categoria', '').strip()
    subcategoria_id= request.GET.get('subcategoria', '').strip()
    estado         = request.GET.get('estado', '').strip()

    # QuerySet base con relaciones para optimizar
    qs = Herencia.objects.select_related(
        'Subcatalogo__catalogo',
        'unidad_medida'
    ).all()

    # Aplicar filtros si vienen
    if nombre:
        qs = qs.filter(nombre__icontains=nombre)
    if categoria_id.isdigit():
        qs = qs.filter(Subcatalogo__catalogo_id=int(categoria_id))
    if subcategoria_id.isdigit():
        qs = qs.filter(Subcatalogo_id=int(subcategoria_id))
    if estado in ['activo', 'inactivo']:
        qs = qs.filter(estado=(estado == 'activo'))

    # Ordenar y paginar (10 por página)
    qs = qs.order_by('nombre')
    page_obj = Paginator(qs, 10).get_page(request.GET.get('page'))

    # Listas para los selects de filtro
    catalogos    = Catalogo.objects.filter(estado=True).order_by('nombre')
    if categoria_id.isdigit():
        subcatalogos = Subcatalogo.objects.filter(
            catalogo_id=int(categoria_id), estado=True
        ).order_by('nombre')
    else:
        subcatalogos = Subcatalogo.objects.filter(estado=True).order_by('nombre')

    # Mensajes flash
    mensaje_exito = request.session.pop('herencia_success', None)
    mensaje_error = request.session.pop('herencia_error', None)

    # Render con contexto
    return render(request, 'inventario/herencias.html', {
        'page_obj':      page_obj,
        'filter': {
            'nombre':      nombre,
            'categoria':   categoria_id,
            'subcategoria':subcategoria_id,
            'estado':      estado,
        },
        'catalogos':     catalogos,
        'subcatalogos':  subcatalogos,
        'mensaje_exito': mensaje_exito,
        'mensaje_error': mensaje_error,
    })

# AGREGAR
@login_required
@supervisor_required
def agregar_herencia(request):
    if request.method == 'POST':
        form = HerenciaForm(request.POST, crear=True)
        if form.is_valid():
            h = form.save(commit=False)
            h.estado = True
            h.save()

            _registrar_log(
                request,
                tabla         = "herencia",
                id_registro   = h.id,
                nombre_modulo = "Inventario",
                nombre_accion = "Crear"
            )
            request.session['herencia_success'] = 'Herencia creada correctamente.'
            return JsonResponse({
                'success':      True,
                'redirect_url': reverse('inventario:lista_herencias')
            })
        else:
            html_form = render_to_string(
                'inventario/modales/fragmento_form_herencia.html',
                {'form': form},
                request=request
            )
            return JsonResponse({'success': False, 'html_form': html_form})
    else:
        form = HerenciaForm(crear=True)
        return render(request,
                        'inventario/modales/modal_agregar_herencia.html',
                        {'form': form, 'crear': True})


# EDITAR
@login_required
@supervisor_required
def editar_herencia(request, pk):
    h = get_object_or_404(Herencia, pk=pk)
    if request.method == 'POST':
        form = HerenciaForm(request.POST, instance=h)
        if form.is_valid():
            form.save()
            _registrar_log(
                request,
                tabla         = "herencia",
                id_registro   = h.id,
                nombre_modulo = "Inventario",
                nombre_accion = "Editar"
            )
            request.session['herencia_success'] = 'Herencia actualizada correctamente.'
            return JsonResponse({
                'success':      True,
                'redirect_url': reverse('inventario:lista_herencias')
            })
        else:
            html_form = render_to_string(
                'inventario/modales/fragmento_form_herencia.html',
                {'form': form, 'herencia': h},
                request=request
            )
            return JsonResponse({'success': False, 'html_form': html_form})
    else:
        form = HerenciaForm(instance=h)
        return render(request,
                        'inventario/modales/modal_editar_herencia.html',
                        {'form': form, 'herencia': h})

# INHABILITAR
@login_required
@supervisor_required
@require_POST
def inhabilitar_herencia(request, pk):
    h = get_object_or_404(Herencia, pk=pk)
    h.estado = False
    h.save(update_fields=['estado'])
    _registrar_log(
        request,
        tabla         = "herencia",
        id_registro   = h.id,
        nombre_modulo = "Inventario",
        nombre_accion = "Inhabilitar"
    )
    request.session['herencia_success'] = 'Herencia inhabilitada correctamente.'
    return JsonResponse({
        'success':      True,
        'redirect_url': reverse('inventario:lista_herencias')
    })
# FIN HERENCIA