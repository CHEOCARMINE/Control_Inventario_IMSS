from django.urls import path
from .views import registrar_usuario, listar_usuarios, ver_usuario, perfil

app_name = 'usuarios'

urlpatterns = [
    path('registrar/', registrar_usuario, name='registrar_usuario'),
    path('lista/', listar_usuarios, name='listar_usuarios'),
    path('ver/<int:pk>/', ver_usuario, name='ver_usuario'),
    path('perfil/', perfil, name='perfil')
]
