from django.http import HttpResponse
from celery import shared_task
from dotenv import load_dotenv

from api.modul.GenerateAnalysGroups import generar_reporte_por_grupo

from .models import CustomUser, Cuestionario, Indicador
from api.modul.analysis import calcular_scores
from celery import shared_task
from api.models import DatosAplicacion
from django.utils.timezone import now
from django.contrib.auth.models import User
#from api.views import generar_reporte_por_grupo  # Importa tu función personalizada
from django.core.mail import send_mail
import logging
import os

load_dotenv()
import logging
logger = logging.getLogger(__name__)


from api.mails import enviar_correo_error, enviar_notificacion_por_correo

DEFAULT_EMAILS = {
    "carrera": "le19080170@merida.tecnm.mx",
    "departamento": "coordinador.sistemas@tecnm.mx",
    "institucion": "le21080997@merida.tecnm.mx",
    "region": "region_user@example.com",
    #"nacion": "le21080997@merida.tecnm.mx",
}

""" 
@shared_task
def calcular_scores_task(user_id, aplicacion_id):
    
    Tarea asíncrona para calcular los scores de un usuario en una aplicación.
    
    # Obtener el usuario y el cuestionario
    usuario = CustomUser.objects.get(id=user_id)
    cuestionario = Cuestionario.objects.get(id=aplicacion_id)
    # Obtener los indicadores del cuestionario
    indicadores = Indicador.objects.filter(cuestionario=cuestionario)
    # Calcular los scores
    scores = calcular_scores(usuario,  indicadores)
    #
    
@shared_task
def check_and_generate_reports():
    # Usuario predeterminado
    default_user = User.objects.get(username='default_user')  # Cambia 'default_user' por tu usuario predeterminado

    # Filtrar aplicaciones cuya fecha límite ha pasado
    aplicaciones_vencidas = DatosAplicacion.objects.filter(fecha_limite__lt=now(), reporte_generado=False)

    for aplicacion in aplicaciones_vencidas:
        try:
            # Generar reporte por grupo para la aplicación vencida
            generar_reporte_por_grupo(usuario=default_user, aplicacion=aplicacion, cuestionario_id=aplicacion.cuestionario.id)
            
            # Marcar como reporte generado
            aplicacion.reporte_generado = True
            aplicacion.save()
        except Exception as e:
            # Loggear errores
            print(f"Error generando reporte para la aplicación {aplicacion.id}: {e}") """

""" DEFAULT_EMAILS = {
    "carrera": "le19080170@merida.tecnm.mx",
    "departamento": "departamento_user@example.com",
    "institucion": "institucion_user@example.com",
    "region": "region_user@example.com",
    "nacion": "nacion_user@example.com",
    
} """



@shared_task
def verificar_y_cerrar_aplicaciones():
    """
    Tarea que verifica las aplicaciones cuya fecha límite ha pasado, las cierra automáticamente,
    y genera reportes para los niveles definidos en DEFAULT_EMAILS.
    """
    try:
        # Filtrar las aplicaciones que cumplen con la condición
        aplicaciones = DatosAplicacion.objects.filter(fecha_limite__lt=now().date(), fecha_fin__isnull=True)
        if not aplicaciones.exists():
            logger.info("No hay aplicaciones para cerrar.")
            return

        # Cachear usuarios necesarios
        usuarios = CustomUser.objects.filter(email__in=DEFAULT_EMAILS.values())
        usuarios_dict = {usuario.email: usuario for usuario in usuarios}

        # Procesar cada aplicación
        for aplicacion in aplicaciones:
            try:
                # Cerrar la aplicación
                aplicacion.fecha_fin = now().date()
                aplicacion.reporte_generado = True
                aplicacion.save()
                logger.info(f"Aplicación cerrada: {aplicacion.cve_aplic}.")

                # Obtener los cuestionarios asociados a la aplicación
                cuestionarios = aplicacion.cuestionario.all()
                if not cuestionarios.exists():
                    logger.warning(f"No cuestionarios asociados a la aplicación {aplicacion.cve_aplic}.")
                    continue
                logger.info(f"Cuestionarios asociados: {[q.cve_cuestionario for q in cuestionarios]}")

                # Generar reportes y enviar correos por nivel
                for nivel, email in DEFAULT_EMAILS.items():
                    usuario = usuarios_dict.get(email)
                    if not usuario:
                        logger.warning(f"Usuario no encontrado para nivel {nivel} con email {email}.")
                        continue

                    try:
                        logger.info(f"Generando reporte para nivel {nivel} con usuario {email}.")
                        resultado = generar_reporte_por_grupo(usuario, aplicacion, cuestionarios.first().cve_cuestionario)

                        if resultado["status"] == "success":
                            enviar_notificacion_por_correo(usuario, nivel, aplicacion)
                            logger.info(f"Reporte generado y notificado para nivel {nivel}.")
                        else:
                            enviar_correo_error(email, nivel, aplicacion, resultado["message"])
                            logger.warning(f"No se pudo generar el reporte para nivel {nivel}: {resultado['message']}")

                    except Exception as e:
                        logger.error(f"Error inesperado al generar el reporte para nivel {nivel}: {e}")
                        enviar_correo_error(email, nivel, aplicacion, str(e))

            except Exception as e:
                logger.error(f"Error al procesar la aplicación {aplicacion.cve_aplic}: {e}")

    except Exception as e:
        logger.error(f"Error general en la tarea verificar_y_cerrar_aplicaciones: {e}")


@shared_task
def generar_reportes_aplicacion_task(aplicacion_id):
    """
    Tarea para generar reportes de todos los usuarios asignados a una aplicación.
    """
    from api.utils import generar_reportes_aplicacion
    resultado = generar_reportes_aplicacion(aplicacion_id)
    return resultado