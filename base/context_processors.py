from login_app.models import Usuario
from usuarios.models import DatosPersonales

def usuario_actual(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return {}
    try:
        u = Usuario.objects.get(id=usuario_id)
        d = DatosPersonales.objects.get(id=u.id_dato)
        full_name = f"{d.nombres} {d.apellido_paterno}{(' ' + d.apellido_materno) if d.apellido_materno else ''}"
        return {'user_full_name': full_name}
    except (Usuario.DoesNotExist, DatosPersonales.DoesNotExist):
        return {}