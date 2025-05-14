from login_app.models import Usuario
from usuarios.models import DatosPersonales

def usuario_actual(request):
    """
    Context processor que inyecta:
        - usuario_actual   : la instancia de Usuario o None
        - user_full_name   : nombre completo para mostrar en el nav
        - is_superadmin    : True si rol == "Super Administrador"
        - is_almacen_admin : True si rol ∈ {"Super Administrador", "Administrador de Almacén"}
        - is_supervisor    : True si rol ∈ {"Super Administrador", "Administrador de Almacén", "Supervisor de Almacén"}
        - can_salida       : True si rol ∈ {todos los roles} (cualquiera puede hacer salidas)
    """
    uid = request.session.get('usuario_id')
    if not uid:
        return {}

    try:
        user = Usuario.objects.select_related('id_rol').get(pk=uid)
        dp   = DatosPersonales.objects.get(pk=user.id_dato)
    except (Usuario.DoesNotExist, DatosPersonales.DoesNotExist):
        return {}

    # Construye el nombre completo
    full_name = f"{dp.nombres} {dp.apellido_paterno}"
    if dp.apellido_materno:
        full_name += f" {dp.apellido_materno}"

    # Calcula permisos según el nombre del rol
    nombre_rol = user.id_rol.nombre
    is_superadmin    = (nombre_rol == "Super Administrador")
    is_almacen_admin = nombre_rol in ("Super Administrador", "Administrador de Almacén")
    is_supervisor    = nombre_rol in ("Super Administrador", "Administrador de Almacén", "Supervisor de Almacén")
    # cualquier rol puede hacer salidas
    can_salida       = nombre_rol in (
        "Super Administrador",
        "Administrador de Almacén",
        "Supervisor de Almacén",
        "Salidas de Almacén",
    )

    return {
        'usuario_actual':     user,
        'user_full_name':     full_name,
        'is_superadmin':      is_superadmin,
        'is_almacen_admin':   is_almacen_admin,
        'is_supervisor':      is_supervisor,
        'can_salida':         can_salida,
    }