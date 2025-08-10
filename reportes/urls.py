from . import views
from django.urls import path

urlpatterns = [
    path("inventario/excel/", views.inventario_excel, name="inventario_excel"),
]