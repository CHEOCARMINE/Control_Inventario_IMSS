"""
URL configuration for Inventario_IMSS project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from login_app.views import login_view, logout_view

urlpatterns = [
    path('admin/', admin.site.urls),

    # Ruta raíz → login
    path('', login_view, name='login'),

    # Logout
    path('logout/', logout_view, name='logout'),

    # CRUD usuarios (solo accesible a SuperAdmin)
    path('usuarios/', include('usuarios.urls', namespace='usuarios')),

    # Rutas de la app base (donde está tu index)
    path('home/', include('base.urls')),

    # Ruta para los Datos de los Solicitantes
    path('solicitantes/', include('solicitantes.urls')),

    # Ruta para los Auxiliares de Inventario
    path('', include('auxiliares_inventario.urls')),

    # Ruta para Inventario
    path('inventario/', include('inventario.urls', namespace='inventario')),
]

