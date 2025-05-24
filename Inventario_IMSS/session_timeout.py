from django.utils import timezone
from django.contrib import messages
from django.shortcuts import redirect

class SessionIdleTimeout:
    def __init__(self, get_response):
        self.get_response = get_response
        # minutos de inactividad antes de expirar
        self.idle_timeout = getattr(__import__('django.conf').conf.settings, 'SESSION_COOKIE_AGE', 120)

    def __call__(self, request):
        if request.session.get('usuario_id'):
            now = timezone.now().timestamp()
            last = request.session.get('last_activity', now)
            if now - last > self.idle_timeout:
                request.session.flush()
                messages.error(
                    request,
                    'Tu sesión expiró por inactividad.',
                    extra_tags='login-danger'
                )
                return redirect('login')
            # actualiza timestamp de última actividad
            request.session['last_activity'] = now

        response = self.get_response(request)
        return response