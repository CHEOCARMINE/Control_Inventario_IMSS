from functools import wraps
from login_app.models import Rol
from django.contrib import messages
from django.shortcuts import redirect
# from login_app.decorators import login_required, superadmin_required, almacen_required, supervisor_required, salidas_required

# Definición de grupos de roles permitidos
ROLE_GROUPS = {
    # Solo Super Administrador @superadmin_required
    "super_admin": ["Super Administrador"],
    # Super Admin + Administrador de Almacén @almacen_required
    "admin_almacen": [
        "Super Administrador",
        "Administrador de Almacén"
    ],
    # Super Admin + Admin Almacén + Supervisor de Almacén @supervisor_required
    "supervisor": [
        "Super Administrador",
        "Administrador de Almacén",
        "Supervisor de Almacén"
    ],
    # Todos los anteriores + Salidas de Almacén @salidas_required
    "salidas": [
        "Super Administrador",
        "Administrador de Almacén",
        "Supervisor de Almacén",
        "Salidas de Almacén"
    ],
}

# @login_required
def login_required(view_func):
    """
    Decorador que comprueba que el usuario haya iniciado sesión.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('usuario_id'):
            messages.error(request, 'Debes iniciar sesión.', extra_tags='login-danger')
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


def role_required(group_key):
    """
    Decorador genérico que comprueba si el rol de la sesión
    está en ROLE_GROUPS[group_key].
    """
    allowed = ROLE_GROUPS.get(group_key, [])
    
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            rol_id = request.session.get('usuario_rol')
            if not rol_id:
                messages.error(request, 'Debes iniciar sesión.', extra_tags='permission-error')
                return redirect('login')
            try:
                nombre_rol = Rol.objects.get(id=rol_id).nombre
            except Rol.DoesNotExist:
                messages.error(request, 'Rol no configurado.', extra_tags='permission-error')
                return redirect('index')
            if nombre_rol not in allowed:
                messages.error(
                    request,
                    'No tienes permiso para acceder a esta sección.',
                    extra_tags='permission-error'
                )
                return redirect('index')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

# Decoradores específicos por grupo
superadmin_required   = role_required("super_admin")
almacen_required      = role_required("admin_almacen")
supervisor_required   = role_required("supervisor")
salidas_required      = role_required("salidas")






