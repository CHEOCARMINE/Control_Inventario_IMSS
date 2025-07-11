from django.urls import path
from . import views

app_name = 'salidas'

urlpatterns = [
    path('productos/', views.productos_para_salida, name='productos_para_salida'),
    path('registrar/', views.registrar_salida, name='registrar_salida'),
]
