from django.apps import AppConfig


class ArvelloappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'arvelloapp'

    def ready(self):
        # Import signals to connect them
        import arvelloapp.signals  # noqa: F401
