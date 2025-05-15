from django.urls import path
from . import views

urlpatterns = [
    # Departamentos
    path('departamentos/', views.lista_departamentos, name='departamentos_lista'),
    path('departamentos/agregar/', views.agregar_departamento, name='departamentos_agregar'),
    path('departamentos/editar/<int:id>/', views.editar_departamento, name='departamentos_editar'),
]
