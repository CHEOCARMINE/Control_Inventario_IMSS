from django.urls import path
from .views import (
    lista_tipo,
    agregar_tipo,
    editar_tipo,
    inhabilitar_tipo,
    lista_productos,
    editar_producto,
    crear_producto,
    registrar_entrada,
    lista_entradas,
    editar_entrada,
)

app_name = 'inventario'

urlpatterns = [
    # ---------------------------------------------------
    # Rutas para TIPOS
    # ---------------------------------------------------
    path('tipos/', lista_tipo, name='lista_tipos'),
    path('tipos/create/', agregar_tipo, name='agregar_tipo'),
    path('tipos/<int:pk>/edit/', editar_tipo, name='editar_tipo'),
    path('tipos/<int:pk>/deactivate/', inhabilitar_tipo, name='inhabilitar_tipo'),

    # ---------------------------------------------------
    # Rutas para PRODUCTOS
    # ---------------------------------------------------
    path('productos/', lista_productos, name='lista_productos'),
    path('productos/create/', crear_producto, name='crear_producto'),    
    path('productos/<int:pk>/edit/', editar_producto, name='editar_producto'),

    # ---------------------------------------------------
    # Rutas para ENTRADAS
    # ---------------------------------------------------
    path('entradas/registrar/', registrar_entrada, name='registrar_entrada'),
    path('entradas/', lista_entradas, name='lista_entradas'),
    path('entradas/<int:pk>/editar/', editar_entrada, name='editar_entrada'),

]
