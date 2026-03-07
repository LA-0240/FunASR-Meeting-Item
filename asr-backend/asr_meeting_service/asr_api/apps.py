from django.apps import AppConfig

class AsrApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'asr_api'

    def ready(self):
        from .models import ready
        ready()