from django.urls import path
from . import views

urlpatterns = [
    path("inventario/excel/", views.inventario_excel, name="inventario_excel"),
]