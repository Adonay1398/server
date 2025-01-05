from __future__ import absolute_import, unicode_literals

# Esto permitirá que Celery se inicialice automáticamente cuando Django se cargue
from .celery import app as celery_app

__all__ = ('celery_app',)
