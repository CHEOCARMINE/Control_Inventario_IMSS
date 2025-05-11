from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.core.paginator   import Paginator
from usuarios.forms import UsuarioForm
from usuarios.models import DatosPersonales
from usuarios.utils import generar_nombre_usuario_unico
from login_app.models import Usuario, Rol
from login_app.decorators import login_required, superadmin_required
from base.models import Modulo, Accion, ReferenciasLog, LogsSistema
from usuarios.validations import (
    validate_letters,
    validate_correo,
    validate_telefono,
    validate_numero_empleado
)

# Crear usuario
@login_required
@superadmin_required
def registrar_usuario(request):
    if request.method == 'POST':
        form = UsuarioForm(request.POST)
        if form.is_valid():
            # Datos del formulario
            nombres = form.cleaned_data['nombres']
            ap_paterno = form.cleaned_data['apellido_paterno']
            ap_materno = form.cleaned_data['apellido_materno']
            correo = form.cleaned_data['correo']
            num_emp = form.cleaned_data['numero_empleado']
            telefono = form.cleaned_data['telefono']
            contraseña = form.cleaned_data['contraseña']
            rol = form.cleaned_data['rol']

            # Validaciones personalizadas
            if not validate_letters(nombres):
                messages.error(request, 'Nombres solo puede contener letras', extra_tags='registro-error')
                return render(request, 'usuarios/crear_usuario.html', {'form': form})

            if not validate_letters(ap_paterno):
                messages.error(request, 'Apellido paterno solo puede contener letras', extra_tags='registro-error')
                return render(request, 'usuarios/crear_usuario.html', {'form': form})

            if ap_materno and not validate_letters(ap_materno, required=False):
                messages.error(request, 'Apellido materno solo puede contener letras', extra_tags='registro-error')
                return render(request, 'usuarios/crear_usuario.html', {'form': form})

            if not validate_correo(correo):
                messages.error(request, 'El correo debe ser institucional: @imssbienestar.gob.mx', extra_tags='registro-error')
                return render(request, 'usuarios/crear_usuario.html', {'form': form})

            if not validate_telefono(telefono):
                messages.error(request, 'El teléfono debe tener exactamente 10 dígitos', extra_tags='registro-error')
                return render(request, 'usuarios/crear_usuario.html', {'form': form})

            if not validate_numero_empleado(num_emp):
                messages.error(
                    request,
                    'Número de empleado inválido. Debe tener 3 letras + 8 números (ej. AAA12345678)',
                    extra_tags='registro-error'
                )
                return render(request, 'usuarios/crear_usuario.html', {'form': form})

            # Chequear unicidad de datos personales
            if DatosPersonales.objects.filter(numero_empleado=num_emp).exists():
                messages.error(request, 'Número de empleado ya registrado.', extra_tags='registro-error')
                return render(request, 'usuarios/crear_usuario.html', {'form': form})

            if DatosPersonales.objects.filter(correo=correo).exists():
                messages.error(request, 'Correo ya registrado.', extra_tags='registro-error')
                return render(request, 'usuarios/crear_usuario.html', {'form': form})

            if telefono and DatosPersonales.objects.filter(telefono=telefono).exists():
                messages.error(request, 'Teléfono ya registrado.', extra_tags='registro-error')
                return render(request, 'usuarios/crear_usuario.html', {'form': form})

            # Guardar DatosPersonales
            datos = DatosPersonales.objects.create(
                nombres = nombres,
                apellido_paterno = ap_paterno,
                apellido_materno = ap_materno,
                correo = correo,
                numero_empleado = num_emp,
                telefono = telefono
            )

            # Generar nombre de usuario único
            primer_nombre = nombres.split()[0]
            nombre_usuario = generar_nombre_usuario_unico(primer_nombre, ap_paterno)

            # Crear Usuario
            u = Usuario.objects.create(
                nombre_usuario = nombre_usuario,
                id_rol = rol,
                id_dato = datos.id,
                estado = True
            )
            u.set_password(contraseña)
            u.save()

            # Referencia de Log
            ref = ReferenciasLog.objects.create(
                tabla = 'login_app_usuario',
                id_registro = u.id
            )

            # Registrar Log de Creación
            modulo = Modulo.objects.get(pk=2)   # 2 = Usuarios
            accion = Accion.objects.get(pk=3)   # 3 = Crear
            LogsSistema.objects.create(
                id_dato = datos.id,
                id_modulo = modulo,
                id_accion = accion,
                id_ref_log = ref,
                ip_origen = request.META.get('REMOTE_ADDR')
            )

            messages.success(
                request,
                f'Usuario "{nombre_usuario}" creado exitosamente.',
                extra_tags='registro-success'
            )
            return redirect('usuarios:registrar_usuario')
        
        else:
            # Capturar errores de validación del Form
            for campo, errores in form.errors.items():
                for err in errores:
                    messages.error(request, f"{campo}: {err}", extra_tags='registro-error')
            return render(request, 'usuarios/crear_usuario.html', {'form': form})

    else:
        form = UsuarioForm()

    return render(request, 'usuarios/crear_usuario.html', {'form': form})

# Lista de Usuarios
@login_required
@superadmin_required
def listar_usuarios(request):
    qs = Usuario.objects.all()

    # extraigo filtros GET
    filtro_u       = request.GET.get('usuario', '').strip()
    filtro_nom     = request.GET.get('nombres', '').strip()
    filtro_ap      = request.GET.get('apellido_paterno', '').strip()
    filtro_am      = request.GET.get('apellido_materno', '').strip()
    filtro_num_emp = request.GET.get('numero_empleado', '').strip()
    filtro_rol     = request.GET.get('rol', '')
    filtro_estado  = request.GET.get('estado', '')

    # aplico filtros sobre qs
    if filtro_u:
        qs = qs.filter(nombre_usuario__icontains=filtro_u)
    if filtro_nom:
        ids = DatosPersonales.objects.filter(nombres__icontains=filtro_nom).values_list('id', flat=True)
        qs = qs.filter(id_dato__in=ids)
    if filtro_ap:
        ids = DatosPersonales.objects.filter(apellido_paterno__icontains=filtro_ap).values_list('id', flat=True)
        qs = qs.filter(id_dato__in=ids)
    if filtro_am:
        ids = DatosPersonales.objects.filter(apellido_materno__icontains=filtro_am).values_list('id', flat=True)
        qs = qs.filter(id_dato__in=ids)
    if filtro_num_emp:
        ids = DatosPersonales.objects.filter(numero_empleado__icontains=filtro_num_emp).values_list('id', flat=True)
        qs = qs.filter(id_dato__in=ids)
    if filtro_rol:
        qs = qs.filter(id_rol__id=filtro_rol)
    if filtro_estado in ['activo', 'inactivo']:
        qs = qs.filter(estado=(filtro_estado == 'activo'))

    # traigo en un solo query todos los DatosPersonales necesarios
    datos_qs = DatosPersonales.objects.filter(id__in=qs.values_list('id_dato', flat=True))
    datos_map = { dp.id: dp for dp in datos_qs }

    # construyo la lista que iteraré en la plantilla
    usuarios_data = []
    for usuario in qs:
        usuarios_data.append({
            'usuario': usuario,
            'datos':   datos_map.get(usuario.id_dato)
        })

    # Paginación: 10 items por página
    paginator   = Paginator(usuarios_data, 10)
    page_number = request.GET.get('page')
    page_obj    = paginator.get_page(page_number)

    # Reconstruir base_url con los filtros (sin el parámetro page)
    params = request.GET.copy()
    params.pop('page', None)
    qs_prefix = '?' + params.urlencode() + ('&' if params else '')

    return render(request, 'usuarios/listar_usuarios.html', {
        'page_obj':   page_obj,
        'roles':      Rol.objects.all(),
        'filter': {
            'usuario':          filtro_u,
            'nombres':          filtro_nom,
            'apellido_paterno': filtro_ap,
            'apellido_materno': filtro_am,
            'numero_empleado':  filtro_num_emp,
            'rol':              filtro_rol,
            'estado':           filtro_estado,
        },
        'qs_prefix': qs_prefix,
    })

# Ver y editar usuarios
@login_required
@superadmin_required
def ver_usuario(request, pk):
    # Trae el usuario y sus datos personales
    u   = get_object_or_404(Usuario, pk=pk)
    dp  = get_object_or_404(DatosPersonales, pk=u.id_dato)
    return render(request, 'usuarios/ver_usuario.html', {
        'usuario': u,
        'datos':    dp,
    })

# Perfil de Usuario
@login_required
def perfil(request):
    # Recuperar usuario y datos personales
    uid = request.session.get('usuario_id')
    u   = Usuario.objects.get(pk=uid)
    dp  = DatosPersonales.objects.get(pk=u.id_dato)

    # Determinar si es un “invitado”
    is_guest = u.nombre_usuario.startswith('Invitado.')

    if request.method == 'POST':
        if is_guest:
            messages.error(request, 'Los usuarios invitados no pueden cambiar la contraseña.', extra_tags='perfil-error')
            return redirect('usuarios:perfil')

        new_pw = request.POST.get('nueva_contrasena', '').strip()
        confirm = request.POST.get('confirm_contrasena', '').strip()

        if not new_pw:
            messages.error(request, 'Por favor ingresa la nueva contraseña.', extra_tags='perfil-error')
        elif new_pw != confirm:
            messages.error(request, 'Las contraseñas no coinciden.', extra_tags='perfil-error')
        else:
            u.set_password(new_pw)
            u.save()
            messages.success(request, 'Contraseña actualizada correctamente.', extra_tags='perfil-success')
            # Renovar la clave de sesión para no desconectar al user
            request.session.cycle_key()

        return redirect('usuarios:perfil')

    return render(request, 'usuarios/perfil.html', {
        'usuario':   u,
        'datos':     dp,
        'is_guest':  is_guest,
    })