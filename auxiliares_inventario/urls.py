from django.urls import path
from .views import lista_catalogos, agregar_catalogo, editar_catalogo, lista_subcatalogos, agregar_subcatalogos, editar_subcatalogos

urlpatterns = [
    path('catalogos/', lista_catalogos,    name='catalogo_list'),
    path('catalogos/create/', agregar_catalogo, name='catalogo_create'),
    path('catalogos/<int:pk>/edit/', editar_catalogo,  name='catalogo_update'),
    path('subcatalogos/',    lista_subcatalogos,   name='subcatalogo_list'),
    path('subcatalogos/add/', agregar_subcatalogos, name='subcatalogo_create'),
    path('subcatalogos/<int:pk>/edit/', editar_subcatalogos, name='subcatalogo_update'),
]