from django.urls import path
from .views import (lista_herencias, agregar_herencia, editar_herencia, inhabilitar_herencia,)

app_name = 'inventario'

urlpatterns = [
    # Listado de herencias
    path('herencias/', lista_herencias, name='lista_herencias'),

    # Crear nueva herencia
    path('herencias/create/', agregar_herencia, name='agregar_herencia'),

    # Editar herencia existente
    path('herencias/<int:pk>/edit/', editar_herencia, name='editar_herencia'),

    # Inhabilitar (soft-delete)
    path('herencias/<int:pk>/deactivate/', inhabilitar_herencia, name='inhabilitar_herencia'),
]
