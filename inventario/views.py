from django.db.models import F
from django.urls import reverse
from django.db import transaction
from django.http import JsonResponse
from django.forms import formset_factory
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from .models import Herencia, Producto, Entrada, EntradaLinea
from django.shortcuts import render, get_object_or_404, redirect
from base.models import Modulo, Accion, ReferenciasLog, LogsSistema
from login_app.decorators import login_required, supervisor_required
from auxiliares_inventario.models import Catalogo, Subcatalogo, Marca
from .forms import (HerenciaForm, ProductoForm, EntradaForm, EntradaLineaFormSet)

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
    nombre          = request.GET.get('nombre', '').strip()
    categoria_id    = request.GET.get('categoria', '').strip()
    subcategoria_id = request.GET.get('subcategoria', '').strip()
    estado          = request.GET.get('estado', '').strip()

    qs = Herencia.objects.select_related('Subcatalogo__catalogo', 'unidad_medida').all()

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

    mensaje_exito = request.session.pop('herencia_success', None)
    mensaje_error = request.session.pop('herencia_error', None)

    return render(request, 'inventario/herencias.html', {
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
# FIN DE HERENCUAS

# PRODUCTOS

# LISTADO
@login_required
@supervisor_required
def lista_productos(request):
    nombre          = request.GET.get('nombre', '').strip()
    categoria_id    = request.GET.get('categoria', '').strip()
    subcategoria_id = request.GET.get('subcategoria', '').strip()
    herencia_id     = request.GET.get('herencia', '').strip()
    estado          = request.GET.get('estado', '').strip()

    qs = Producto.objects.select_related(
        'herencia__Subcatalogo__catalogo',
        'marca'
    ).all()

    if nombre:
        qs = qs.filter(nombre__icontains=nombre)
    if herencia_id.isdigit():
        qs = qs.filter(herencia_id=int(herencia_id))
    if estado in ['activo', 'inactivo']:
        qs = qs.filter(estado=(estado == 'activo'))

    if categoria_id.isdigit():
        qs = qs.filter(herencia__Subcatalogo__catalogo_id=int(categoria_id))
    if subcategoria_id.isdigit():
        qs = qs.filter(herencia__Subcatalogo_id=int(subcategoria_id))

    qs = qs.order_by(
        'herencia__Subcatalogo__catalogo__nombre',
        'herencia__Subcatalogo__nombre',
        'herencia__nombre',
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

    herencias_qs = Herencia.objects.filter(estado=True).select_related(
        'Subcatalogo__catalogo'
    )
    if subcategoria_id.isdigit():
        herencias_qs = herencias_qs.filter(Subcatalogo_id=int(subcategoria_id))
    elif categoria_id.isdigit():
        herencias_qs = herencias_qs.filter(Subcatalogo__catalogo_id=int(categoria_id))
    herencias = herencias_qs.order_by(
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
            'herencia':     herencia_id,
            'estado':       estado,
        },
        'catalogos':     catalogos,
        'subcatalogos':  subcatalogos,
        'herencias':     herencias,
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
                {'form': form, 'producto': prod},
                request=request
            )
            return JsonResponse({'success': False, 'html_form': html})
    else:
        form = ProductoForm(instance=prod)
        return render(request,
                        'inventario/modales/modal_editar_producto.html',
                        {'form': form, 'producto': prod})

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

@login_required
@supervisor_required
def registrar_entrada(request):
    if request.method == 'POST':
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

                    producto.stock = producto.stock + cantidad
                    producto.save(update_fields=['stock'])

            return JsonResponse({
                'success':      True,
                'redirect_url': reverse('inventario:lista_productos')
            })

        else:
            html_form = render_to_string(
                'inventario/modales/fragmento_form_entrada.html',
                {
                    'form_entrada':   form_entrada,
                    'formset_lineas': formset_lineas,
                    'todos_productos': Producto.objects.all().order_by(
                        'herencia__Subcatalogo__catalogo__nombre',
                        'herencia__Subcatalogo__nombre',
                        'herencia__nombre',
                        'nombre'
                    )
                },
                request=request
            )
            return JsonResponse({'success': False, 'html_form': html_form})

    else:
        form_entrada   = EntradaForm()
        formset_lineas = EntradaLineaFormSet()

        todos_productos = Producto.objects.all().order_by(
            'herencia__Subcatalogo__catalogo__nombre',
            'herencia__Subcatalogo__nombre',
            'herencia__nombre',
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