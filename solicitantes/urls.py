from . import views
from django.urls import path

urlpatterns = [
    # Departamentos
    path('departamentos/', views.lista_departamentos, name='departamentos_lista'),
    path('departamentos/agregar/', views.agregar_departamento, name='departamentos_agregar'),
    path('departamentos/editar/<int:id>/', views.editar_departamento, name='departamentos_editar'),
    # Unidades
    path('unidades/', views.lista_unidades, name='unidades_lista'),
    path('unidades/agregar/', views.agregar_unidad, name='unidades_agregar'),
    path('unidades/editar/<int:id>/', views.editar_unidad, name='unidades_editar'),
]
