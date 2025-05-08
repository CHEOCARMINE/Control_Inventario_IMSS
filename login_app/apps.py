from django.apps import AppConfig

class LoginAppConfig(AppConfig):
    name = 'login_app'

    def ready(self):
        import login_app.signals