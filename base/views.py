from django.shortcuts import render, redirect
from login_app.decorators import login_required
from django.contrib import messages

@login_required
def index(request):
    if not request.session.get('usuario_id'):
        messages.error(request, 'Debes iniciar sesión primero.', extra_tags='login-danger')
        return redirect('login')
    return render(request, 'base/index.html')