from django.urls import path
from .views import (
    lista_herencias,
    agregar_herencia,
    editar_herencia,
    inhabilitar_herencia,
    lista_productos,
    editar_producto,
    crear_producto,
    registrar_entrada,
)

app_name = 'inventario'

urlpatterns = [
    # ---------------------------------------------------
    # Rutas para HERENCIAS
    # ---------------------------------------------------
    path('herencias/', lista_herencias, name='lista_herencias'),
    path('herencias/create/', agregar_herencia, name='agregar_herencia'),
    path('herencias/<int:pk>/edit/', editar_herencia, name='editar_herencia'),
    path('herencias/<int:pk>/deactivate/', inhabilitar_herencia, name='inhabilitar_herencia'),

    # ---------------------------------------------------
    # Rutas para PRODUCTOS
    # ---------------------------------------------------
    path('productos/', lista_productos, name='lista_productos'),
    path('productos/create/', crear_producto, name='crear_producto'),    
    path('productos/<int:pk>/edit/', editar_producto, name='editar_producto'),

    # ---------------------------------------------------
    # Rutas para ENTRADAS
    # ---------------------------------------------------
    # Registrar Entrada con varias líneas (modal AJAX)
    path('entradas/registrar/', registrar_entrada, name='registrar_entrada'),
]
