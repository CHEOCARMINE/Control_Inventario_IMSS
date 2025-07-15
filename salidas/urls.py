from django.urls import path
from . import views

app_name = 'salidas'

urlpatterns = [
    path('productos/', views.productos_para_salida, name='productos_para_salida'),
    path('registrar/', views.registrar_salida, name='registrar_salida'),
    path('', views.lista_salidas, name='lista_salidas'),
    path('vale/<int:pk>/entregar/', views.entregar_vale, name='entregar_vale'),
    path('vale/<int:pk>/cancelar/',  views.cancelar_vale,  name='cancelar_vale'),
]
