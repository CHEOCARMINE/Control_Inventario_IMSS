from django.urls import path
from .views import lista_catalogos, agregar_catalogo, editar_catalogo

urlpatterns = [
    path('catalogos/', lista_catalogos,    name='catalogo_list'),
    path('catalogos/create/', agregar_catalogo, name='catalogo_create'),
    path('catalogos/<int:pk>/edit/', editar_catalogo,  name='catalogo_update'),
]