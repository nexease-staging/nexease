from django.apps import AppConfig
class SaaSConfig(AppConfig):
    name = 'apps.saas'
    def ready(self):
        from .entitlements import install_guards
        install_guards()
