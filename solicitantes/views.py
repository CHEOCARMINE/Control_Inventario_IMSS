from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from base.models import Modulo, Accion, ReferenciasLog, LogsSistema
from .models import Departamento
from login_app.decorators import login_required, almacen_required
from .forms import DepartamentoForm

# Lista de Departamentos
@login_required
@almacen_required
def lista_departamentos(request):
    nombre = request.GET.get('nombre', '')
    estado = request.GET.get('estado', '')

    departamentos = Departamento.objects.all()

    # Filtros
    if nombre:
        departamentos = departamentos.filter(nombre__icontains=nombre)
    if estado:
        if estado == 'activo':
            departamentos = departamentos.filter(estado=True)
        elif estado == 'inactivo':
            departamentos = departamentos.filter(estado=False)

    # Orden y paginación
    departamentos = departamentos.order_by('nombre')
    paginator = Paginator(departamentos, 10)  # 10 por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Para conservar los filtros en la paginación
    qs_prefix = '?'
    if nombre:
        qs_prefix += f'nombre={nombre}&'
    if estado:
        qs_prefix += f'estado={estado}&'

    context = {
        'page_obj': page_obj,
        'filter': {
            'nombre': nombre,
            'estado': estado
        },
        'qs_prefix': qs_prefix
    }

    # Captura y borra mensajes de sesión si existen
    mensaje_exito = request.session.pop('departamento-success', None)
    mensaje_error = request.session.pop('departamento-error', None)

    context = {
        'page_obj': page_obj,
        'filter': {
            'nombre': nombre,
            'estado': estado
        },
        'qs_prefix': qs_prefix,
        'mensaje_exito': mensaje_exito,
        'mensaje_error': mensaje_error,
    }

    return render(request, 'solicitantes/departamentos.html', context)

# Agregar Departamentos
@login_required
@almacen_required
def agregar_departamento(request):
    if request.method == 'POST':
        form = DepartamentoForm(request.POST)
        if form.is_valid():
            departamento = form.save(commit=False)
            departamento.estado = True
            departamento.save()

            # Registrar Log de creación
            ref = ReferenciasLog.objects.create(tabla="departamento", id_registro=departamento.id)
            modulo = Modulo.objects.get(nombre='Auxiliares')
            accion = Accion.objects.get(nombre='Crear')
            LogsSistema.objects.create(
                id_dato=request.user.id_dato,
                id_modulo=modulo,
                id_accion=accion,
                id_ref_log=ref,
                ip_origen=request.META.get('REMOTE_ADDR')
            )

            request.session['departamento-success'] = 'Departamento agregado correctamente.'
            return JsonResponse({'success': True})
        else:
            from django.template.loader import render_to_string
            html_form = render_to_string(
                'solicitantes/modales/fragmento_form_departamento.html',
                {'form': form},
                request=request
            )
            return JsonResponse({'success': False, 'html_form': html_form})
    else:
        form = DepartamentoForm()
        form.fields.pop('estado')
        return render(request, 'solicitantes/modales/modal_agregar_departamento.html', {'form': form})

# Editar Departamento
@login_required
@almacen_required
def editar_departamento(request, id):
    departamento = get_object_or_404(Departamento, id=id)

    if request.method == 'POST':
        form = DepartamentoForm(request.POST, instance=departamento)
        if form.is_valid():
            form.save()

            # Registrar Log de edición
            ref = ReferenciasLog.objects.create(tabla="departamento", id_registro=departamento.id)
            modulo = Modulo.objects.get(nombre='Auxiliares')
            accion = Accion.objects.get(nombre='Editar')
            LogsSistema.objects.create(
                id_dato=request.user.id_dato,
                id_modulo=modulo,
                id_accion=accion,
                id_ref_log=ref,
                ip_origen=request.META.get('REMOTE_ADDR')
            )

            request.session['departamento-success'] = 'Departamento actualizado correctamente.'
            return JsonResponse({'success': True})
        else:
            from django.template.loader import render_to_string
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
