## Control de Inventario IMSS
Aplicación web de gestión de inventarios para IMSS Bienestar, desarrollada en Django.

## Requisitos
- Python 3.9+
- Django 5.2
- Virtualenv (opcional, pero recomendable)

## Instalación
1. **Clonar el repositorio**

```git clone https://github.com/CHEOCARMINE/Control_Inventario_IMSS.git ```

```cd Control_Inventario_IMSS ```

2. **Crear y activar entorno virtual**
   
```python -m venv venv ```

```## Windows ```

```venv\Scripts\activate ```

```## macOS/Linux ```

```source venv/bin/activate ```

4. **Instalar dependencias**
   
```pip install -r requirements.txt ```

6. **Configurar variables de entorno**
   
```cp .env.example .env ```
## Rellena .env con tus credenciales y settings locales

1. **Aplicar migraciones y poblar datos iniciales**
   
```python manage.py migrate ```

Al hacerlo, las señales (post_migrate) crearán automáticamente:
- Roles básicos (4)
- DatosPersonales “Invitado” (4)
- Usuarios “Invitado.Rol” (4)
- Módulos y Acciones para auditoría (7 de cada uno)

2. **Crear superusuario (opcional)**
   
```python manage.py createsuperuser```

3. **Levantar servidor de desarrollo**
   
```python manage.py runserver ```

Abre tu navegador en http://127.0.0.1:8000/.

## Población inicial de datos
Tras aplicar migraciones se generan automáticamente:

- Roles: Super Administrador, Administrador de Almacén, Supervisor de Almacén, Salidas de Almacén
- Datos y Usuarios Invitados: un usuario invitado por cada rol con contraseña por defecto
- Módulos y Acciones utilizados en la auditoría del sistema

## Credenciales iniciales

Para acceder tras la migración, usa la cuenta invitado correspondiente:

- **Invitado.SuperAdministrador**
- **Invitado.AdministradordeAlmacén** 
- **Invitado.SupervisordeAlmacén**
- **Invitado.SalidasdeAlmacén**

Todas con contraseña: 0123456789

## Recomendaciones

1. Inicia sesión con el usuario Invitado.SuperAdministrador.
2. Crea tu propia cuenta de usuario con rol de SuperAdministrador.
3. Cierra sesión e ingresa con la cuenta recién creada.
4. Desactiva los usuarios invitados y cambia las contraseñas por seguridad.
