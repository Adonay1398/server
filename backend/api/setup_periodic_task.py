from django_celery_beat.models import PeriodicTask, IntervalSchedule

def setup_periodic_task():
    """
    Configura la tarea periódica para verificar y cerrar aplicaciones.
    """
    schedule, _ = IntervalSchedule.objects.get_or_create(
        every=1,  # Cada 60 minutos
        period=IntervalSchedule.DAYS,
    )

    PeriodicTask.objects.get_or_create(
        interval=schedule,
        name="Verificar y cerrar aplicaciones",
        task="api.tasks.verificar_y_cerrar_aplicaciones",
    )
