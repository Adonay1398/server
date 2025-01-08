""" from django.apps import AppConfig
from .tasks import setup_periodic_task


class ApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "api"

    def ready(self):
        # Importar y configurar la tarea periódica
        from .tasks import setup_periodic_task
        setup_periodic_task()
 """