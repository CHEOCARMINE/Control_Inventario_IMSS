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
    # Solicitantes
    path('', views.lista_solicitantes, name='solicitantes_lista'),
    path('agregar/', views.agregar_solicitante, name='solicitantes_agregar'),
    path('editar/<int:id>/', views.editar_solicitante, name='solicitantes_editar'),
    path('ajax/departamentos/', views.ajax_departamentos_por_unidad, name='ajax_departamentos_por_unidad'),
]
