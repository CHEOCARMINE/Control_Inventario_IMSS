from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from django.conf import settings
from django.contrib.sessions.models import Session
from login_app.models import Usuario
from base.models import Modulo, Accion, LogsSistema


def login_view(request):
    # si la URL llega con expired=1, lanza tu alerta de expiración
    if request.GET.get('expired') == '1':
        messages.error(
        request,
        'Tu sesión expiró por inactividad.',
        extra_tags='login-danger'
    )
    
    # Si ya hay sesión abierta, redirige al index
    if request.session.get('usuario_id'):
        return redirect('index')

    if request.method == 'POST':
        nombre_usuario = request.POST.get('nombre_usuario')
        contraseña     = request.POST.get('contraseña')

        # Buscar usuario
        try:
            u = Usuario.objects.get(nombre_usuario=nombre_usuario)
        except Usuario.DoesNotExist:
            messages.error(request, 'Usuario no encontrado.', extra_tags='login-danger')
            return redirect('login')

        # Verificar estado
        if not u.estado:
            messages.error(request, 'Cuenta desactivada.', extra_tags='login-danger')
            return redirect('login')

        # Verificar contraseña
        if not u.check_password(contraseña):
            messages.error(request, 'Contraseña incorrecta.', extra_tags='login-danger')
            return redirect('login')

        # INVALIDAR SESIONES PREVIAS (solo una sesión activa a la vez)
        prev_key = getattr(u, 'session_key', None)
        if prev_key:
            Session.objects.filter(session_key=prev_key).delete()

        # Regenerar clave de sesión (previene fijación)
        request.session.cycle_key()

        # Guardar datos en sesión
        request.session['usuario_id']  = u.id
        request.session['usuario_rol'] = u.id_rol_id

        # Almacenar esta sesión en el usuario
        u.session_key = request.session.session_key
        u.save(update_fields=['session_key'])

        # Registrar log de “Iniciar Sesión”
        modulo = Modulo.objects.get(nombre="Login")
        accion = Accion.objects.get(nombre="Iniciar Sesión")
        LogsSistema.objects.create(
            id_dato    = u.id_dato,
            id_modulo  = modulo,
            id_accion  = accion,
            id_ref_log = None,
            fecha_evento = None,                 # si usas auto_now_add, lo omites
            ip_origen  = request.META.get('REMOTE_ADDR'),
        )

        return redirect('index')

    # GET → mostrar formulario
    return render(request, 'login_app/login.html')


def logout_view(request):
    # Antes de destruir la sesión, registra el log
    usuario_id = request.session.get('usuario_id')
    if usuario_id:
        try:
            u = Usuario.objects.get(pk=usuario_id)
            modulo = Modulo.objects.get(nombre="Login")
            accion = Accion.objects.get(nombre="Cerrar Sesión")
            LogsSistema.objects.create(
                id_dato    = u.id_dato,
                id_modulo  = modulo,
                id_accion  = accion,
                id_ref_log = None,
                ip_origen  = request.META.get('REMOTE_ADDR'),
            )
        except Usuario.DoesNotExist:
            pass

    # Cerrar sesión completamente
    request.session.flush()
    return redirect('login')
