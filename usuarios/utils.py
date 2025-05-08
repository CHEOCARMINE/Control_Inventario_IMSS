from login_app.models import Usuario


def generar_nombre_usuario_unico(primer_nombre: str, apellido_paterno: str) -> str:
    """
    Construye un nombre de usuario base "PrimerNombre.ApellidoPaterno".
    Si ya existe, le añade un sufijo incremental: .1, .2, ...

    Ejemplo:
      - Invitado.Rol
      - Invitando.Rol.1
      - Invitado.Rol.2
    """
    # Base sin espacios
    base = f"{primer_nombre}.{apellido_paterno}".replace(" ", "")

    # Si no existe, retornamos la base
    if not Usuario.objects.filter(nombre_usuario=base).exists():
        return base

    # Si existe, buscamos el siguiente sufijo
    contador = 1
    while True:
        candidato = f"{base}.{contador}"
        if not Usuario.objects.filter(nombre_usuario=candidato).exists():
            return candidato
        contador += 1
