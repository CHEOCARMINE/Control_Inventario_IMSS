from django.urls import path
from .views import registrar_usuario

urlpatterns = [
    path('registrar/', registrar_usuario, name='registrar_usuario'),
]
