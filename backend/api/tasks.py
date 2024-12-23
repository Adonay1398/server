from celery import shared_task
from .models import CustomUser, Cuestionario, Indicador
from api.modul.analysis import calcular_scores

@shared_task
def calcular_scores_task(user_id, aplicacion_id):
    """
    Tarea asíncrona para calcular los scores de un usuario en una aplicación.
    """
    # Obtener el usuario y el cuestionario
    usuario = CustomUser.objects.get(id=user_id)
    cuestionario = Cuestionario.objects.get(id=aplicacion_id)
    # Obtener los indicadores del cuestionario
    indicadores = Indicador.objects.filter(cuestionario=cuestionario)
    # Calcular los scores
    scores = calcular_scores(usuario,  indicadores)
    #