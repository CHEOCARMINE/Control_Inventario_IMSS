from django.db.models import Q
from django.urls import reverse
from .models import Departamento
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.shortcuts import render, get_object_or_404
from .models import Departamento, Unidad, Solicitante, Cargo
from .forms import DepartamentoForm, UnidadForm, SolicitanteForm
from login_app.decorators import login_required, almacen_required
from base.models import Modulo, Accion, ReferenciasLog, LogsSistema

# Helper de logs
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

# Inicio de Departamentos
# Lista 
@login_required
@almacen_required
def lista_departamentos(request):
    nombre = request.GET.get('nombre', '')
    estado = request.GET.get('estado', '')

    qs = Departamento.objects.all()
    if nombre:
        qs = qs.filter(nombre__icontains=nombre)
    if estado:
        qs = qs.filter(estado=(estado == 'activo'))

    page_obj = Paginator(qs.order_by('nombre'), 10).get_page(request.GET.get('page'))

    mensaje_exito = request.session.pop('departamento-success', None)
    mensaje_error = request.session.pop('departamento-error', None)

    return render(request, 'solicitantes/departamentos.html', {
        'page_obj': page_obj,
        'filter': {'nombre': nombre, 'estado': estado},
        'mensaje_exito': mensaje_exito,
        'mensaje_error': mensaje_error,
    })

# Agregar 
@login_required
@almacen_required
def agregar_departamento(request):
    if request.method == 'POST':
        form = DepartamentoForm(request.POST, crear=True)
        if form.is_valid():
            departamento = form.save(commit=False)
            departamento.estado = True
            departamento.save()

            _registrar_log(
                request,
                tabla="departamento",
                id_registro=departamento.id,
                nombre_modulo="Auxiliares",
                nombre_accion="Crear"
            )

            request.session['departamento-success'] = 'Departamento agregado correctamente.'
            return JsonResponse({
                'success': True,
                'redirect_url': reverse('departamentos_lista')
            })
        else:
            html_form = render_to_string(
                'solicitantes/modales/fragmento_form_departamento.html',
                {'form': form},
                request=request
            )
            return JsonResponse({'success': False, 'html_form': html_form})
    else:
        form = DepartamentoForm(crear=True)
        return render(request, 'solicitantes/modales/modal_agregar_departamento.html', {
            'form': form
        })

# Editar
@login_required
@almacen_required
def editar_departamento(request, id):
    departamento = get_object_or_404(Departamento, id=id)

    if request.method == 'POST':
        form = DepartamentoForm(request.POST, instance=departamento)
        if form.is_valid():
            departamento = form.save()

            _registrar_log(
                request,
                tabla="departamento",
                id_registro=departamento.id,
                nombre_modulo="Auxiliares",
                nombre_accion="Editar"
            )

            request.session['departamento-success'] = 'Departamento actualizado correctamente.'
            return JsonResponse({
                'success': True,
                'redirect_url': reverse('departamentos_lista')
            })
        else:
            html_form = render_to_string(
                'solicitantes/modales/fragmento_form_departamento.html',
                {'form': form, 'departamento': departamento},
                request=request
            )
            return JsonResponse({'success': False, 'html_form': html_form})
    else:
        form = DepartamentoForm(instance=departamento)
        return render(request, 'solicitantes/modales/modal_editar_departamento.html', {
            'form': form,
            'departamento': departamento
        })
# Fin de Departamentos

# Inicio de Unidad
# Lista
@login_required
@almacen_required
def lista_unidades(request):
    nombre    = request.GET.get('nombre', '')
    clues     = request.GET.get('clues', '')
    dep_id    = request.GET.get('departamento', '')
    estado    = request.GET.get('estado', '')

    qs = Unidad.objects.all()
    if nombre:
        qs = qs.filter(nombre__icontains=nombre)
    if clues:
        qs = qs.filter(clues__icontains=clues)
    if dep_id:
        qs = qs.filter(departamentos__id=dep_id)
    if estado:
        qs = qs.filter(estado=(estado == 'activo'))

    page_obj = Paginator(qs.order_by('nombre'), 10).get_page(request.GET.get('page'))

    mensaje_exito = request.session.pop('unidad-success', None)
    mensaje_error = request.session.pop('unidad-error', None)

    # Para el filtro de departamentos
    departamentos = Departamento.objects.filter(estado=True).order_by('nombre')

    return render(request, 'solicitantes/unidades.html', {
        'page_obj': page_obj,
        'filter': {
            'nombre': nombre,
            'clues': clues,
            'departamento': dep_id,
            'estado': estado,
        },
        'departamentos': departamentos,
        'mensaje_exito': mensaje_exito,
        'mensaje_error': mensaje_error,
    })

# Agregar
@login_required
@almacen_required
def agregar_unidad(request):
    if request.method == 'POST':
        form = UnidadForm(request.POST, crear=True)
        if form.is_valid():
            unidad = form.save()
            unidad.estado = True
            unidad.save()

            _registrar_log(
                request,
                tabla="unidad",
                id_registro=unidad.id,
                nombre_modulo="Auxiliares",
                nombre_accion="Crear"
            )

            request.session['unidad-success'] = 'Unidad agregada correctamente.'
            return JsonResponse({
                'success': True,
                'redirect_url': reverse('unidades_lista')
            })
        else:
            html_form = render_to_string(
                'solicitantes/modales/fragmento_form_unidad.html',
                {'form': form},
                request=request
            )
            return JsonResponse({'success': False, 'html_form': html_form})
    else:
        form = UnidadForm(crear=True)
        return render(request, 'solicitantes/modales/modal_agregar_unidad.html', {
            'form': form
        })

# Editar
@login_required
@almacen_required
def editar_unidad(request, id):
    unidad = get_object_or_404(Unidad, id=id)

    if request.method == 'POST':
        form = UnidadForm(request.POST, instance=unidad)
        if form.is_valid():
            unidad = form.save()


            _registrar_log(
                request,
                tabla="unidad",
                id_registro=unidad.id,
                nombre_modulo="Auxiliares",
                nombre_accion="Editar"
            )

            request.session['unidad-success'] = 'Unidad actualizada correctamente.'
            return JsonResponse({
                'success': True,
                'redirect_url': reverse('unidades_lista')
            })
        else:
            html_form = render_to_string(
                'solicitantes/modales/fragmento_form_unidad.html',
                {'form': form, 'unidad': unidad},
                request=request
            )
            return JsonResponse({'success': False, 'html_form': html_form})
    else:
        form = UnidadForm(instance=unidad)
        return render(request, 'solicitantes/modales/modal_editar_unidad.html', {
            'form': form,
            'unidad': unidad
        })
# Fin de Unidad

# Inicio de Solicitantes
# Lista
@login_required
@almacen_required
def lista_solicitantes(request):
    nombre       = request.GET.get('nombre', '')
    cargo = request.GET.get('cargo', '')
    unidad_id    = request.GET.get('unidad', '')
    depto_id     = request.GET.get('departamento', '')
    estado       = request.GET.get('estado', '')

    qs = Solicitante.objects.select_related('cargo', 'unidad', 'departamento')
    if nombre:
        qs = qs.filter(nombre__icontains=nombre)
    if cargo:
        qs = qs.filter(cargo__id=cargo)
    if unidad_id:
        qs = qs.filter(unidad_id=unidad_id)
    if depto_id:
        qs = qs.filter(departamento_id=depto_id)
    if estado:
        qs = qs.filter(estado=(estado == 'activo'))

    page_obj = Paginator(qs.order_by('nombre'), 10).get_page(request.GET.get('page'))

    cargos        = Cargo.objects.order_by('nombre')
    unidades      = Unidad.objects.filter(estado=True).order_by('nombre')
    departamentos = Departamento.objects.filter(estado=True).order_by('nombre')

    mensaje_exito = request.session.pop('solicitante-success', None)
    mensaje_error = request.session.pop('solicitante-error',   None)

    return render(request, 'solicitantes/solicitantes.html', {
        'page_obj': page_obj,
        'filter': {
            'nombre':       nombre,
            'cargo':        cargo,
            'unidad':       unidad_id,
            'departamento': depto_id,
            'estado':       estado,
        },
        'cargos':        cargos,
        'unidades':      unidades,
        'departamentos': departamentos,
        'mensaje_exito': mensaje_exito,
        'mensaje_error': mensaje_error,
    })

# Agregar
@login_required
@almacen_required
def agregar_solicitante(request):
    if request.method == 'POST':
        form = SolicitanteForm(request.POST, crear=True)
        if form.is_valid():
            solicitante = form.save()
            _registrar_log(
                request,
                tabla='solicitante',
                id_registro=solicitante.id,
                nombre_modulo='Auxiliares',
                nombre_accion='Crear'
            )
            request.session['solicitante-success'] = 'Solicitante agregado correctamente.'
            return JsonResponse({
                'success': True,
                'redirect_url': reverse('solicitantes_lista')
            })
        # Si hay errores, devolvemos sólo el fragmento del form
        html_form = render_to_string(
            'solicitantes/modales/fragmento_form_solicitante.html',
            {'form': form, 'cargos': Cargo.objects.order_by('nombre'),},
            request=request
        )
        return JsonResponse({'success': False, 'html_form': html_form})
    else:
        # GET: sólo render del modal con el form vacío
        form = SolicitanteForm(crear=True)
        return render(request, 'solicitantes/modales/modal_agregar_solicitante.html', {'form': form})

# Editar
@login_required
@almacen_required
def editar_solicitante(request, id):
    sol = get_object_or_404(Solicitante, id=id)
    if request.method == 'POST':
        form = SolicitanteForm(request.POST, instance=sol)
        if form.is_valid():
            sol = form.save()
            _registrar_log(
                request,
                tabla='solicitante',
                id_registro=sol.id,
                nombre_modulo='Auxiliares',
                nombre_accion='Editar'
            )
            request.session['solicitante-success'] = 'Solicitante actualizado correctamente.'
            return JsonResponse({
                'success': True,
                'redirect_url': reverse('solicitantes_lista')
            })
        html_form = render_to_string(
            'solicitantes/modales/fragmento_form_solicitante.html',
            {'form': form, 'solicitante': sol, 'cargos': Cargo.objects.order_by('nombre'),},
            request=request
        )
        return JsonResponse({'success': False, 'html_form': html_form})
    else:
        form = SolicitanteForm(instance=sol)
        return render(request, 'solicitantes/modales/modal_editar_solicitante.html', {'form': form, 'solicitante': sol})

# Endpoint AJAX para Departamentos
@login_required
@almacen_required
def ajax_departamentos_por_unidad(request):
    unidad_id = request.GET.get('unidad_id')
    qs = Departamento.objects.none()
    if unidad_id:
        qs = Departamento.objects.filter(
            unidades__id=unidad_id,
            estado=True
        ).order_by('nombre')
    data = [{'id': d.id, 'nombre': d.nombre} for d in qs]
    return JsonResponse(data, safe=False)
# Fin de Solicitante