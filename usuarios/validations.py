import re

# Solo letras
def validate_letters(text, required=True):
    pattern = r'^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$' if required else r'^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]*$'
    return bool(re.match(pattern, text))

# Correo institucional
def validate_correo(correo):
    return correo.endswith('@imssbienestar.gob.mx')

# Teléfono
def validate_telefono(telefono):
    return telefono.isdigit() and len(telefono) == 10

# Número de empleado: 3 letras + 8 números
def validate_numero_empleado(numero):
    pattern = r'^[A-Za-z]{3}\d{8}$'
    return bool(re.match(pattern, numero))