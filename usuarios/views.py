from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from usuarios.forms import UsuarioForm
from usuarios.models import DatosPersonales
from usuarios.utils import generar_nombre_usuario_unico
from login_app.models import Usuario
from login_app.decorators import login_required, superadmin_required
from base.models import Modulo, Accion, ReferenciasLog, LogsSistema
from usuarios.validations import (
    validate_letters,
    validate_correo,
    validate_telefono,
    validate_numero_empleado
)

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
                contraseña = make_password(contraseña),
                id_rol = rol,
                id_dato = datos.id,
                estado = True
            )

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
            return redirect('registrar_usuario')
        
        else:
            # Capturar errores de validación del Form
            for campo, errores in form.errors.items():
                for err in errores:
                    messages.error(request, f"{campo}: {err}", extra_tags='registro-error')
            return render(request, 'usuarios/crear_usuario.html', {'form': form})

    else:
        form = UsuarioForm()

    return render(request, 'usuarios/crear_usuario.html', {'form': form})
