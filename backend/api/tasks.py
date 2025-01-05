from celery import shared_task
from .models import CustomUser, Cuestionario, Indicador
from api.modul.analysis import calcular_scores
from celery import shared_task
from api.models import DatosAplicacion
from django.utils.timezone import now
from django.contrib.auth.models import User
from api.views import generar_reporte_por_grupo  # Importa tu función personalizada
from django.core.mail import send_mail
import logging
logger = logging.getLogger(__name__)

DEFAULT_EMAILS = {
    "carrera": "le1908017@merida.tecnm.mx",
    "departamento": "departamento_user@example.com",
    "institucion": "institucion_user@example.com",
    "region": "region_user@example.com",
    "nacion": "nacion_user@example.com",
}

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
            print(f"Error generando reporte para la aplicación {aplicacion.id}: {e}")


def enviar_notificacion_por_correo(usuario, nivel, aplicacion):
    """
    Envía un correo notificando la generación del reporte.
    """
    asunto = f"Reporte generado para el nivel {nivel}"
    mensaje = (
        f"Hola {usuario.first_name},\n\n"
        f"Se ha generado un reporte para la aplicación {aplicacion.cve_aplic} "
        f"en el nivel {nivel}.\n\n"
        "Saludos,\nEl equipo."
    )
    send_mail(asunto, mensaje, 'admin@example.com', [usuario.email])

@shared_task
def verificar_y_cerrar_aplicaciones():
    """
    Tarea que verifica las aplicaciones cuya fecha límite ha pasado, las cierra automáticamente,
    y genera reportes para los niveles definidos en DEFAULT_EMAILS.
    """
    try:
        aplicaciones = DatosAplicacion.objects.filter(fecha_limite__lt=now().date(), fecha_fin__isnull=True)
        if not aplicaciones.exists():
            logger.info("No hay aplicaciones para cerrar.")
            return

        for aplicacion in aplicaciones:
            try:
                # Cerrar la aplicación
                aplicacion.fecha_fin = now().date()
                aplicacion.reporte_generado = True
                aplicacion.save()
                logger.info(f"Closed application {aplicacion.cve_aplic}.")

                # Obtener los cuestionarios asociados a la aplicación
                cuestionarios = aplicacion.cuestionario.all()
                if not cuestionarios.exists():
                    logger.warning(f"No se encontraron cuestionarios asociados a la aplicación {aplicacion.cve_aplic}.")
                    continue
                logger.info(f"Cuestionarios asociados: {[q.cve_cuestionario for q in cuestionarios]}")

                # Generar reportes para cada nivel
                for nivel, email in DEFAULT_EMAILS.items():
                    try:
                        usuario = CustomUser.objects.filter(email=email).first()
                        if not usuario:
                            logger.warning(f"Usuario no encontrado para nivel {nivel} con email {email}.")
                            continue

                        logger.info(f"Generando reporte para nivel {nivel} con usuario {email}.")
                        generar_reporte_por_grupo(usuario, aplicacion, cuestionarios.first().cve_cuestionario)
                        logger.info(f"Reporte generado para nivel {nivel}.")
                        enviar_notificacion_por_correo(usuario, nivel, aplicacion)
                        logger.info(f"Correo enviado a {email} para nivel {nivel}.")

                    except Exception as e:
                        logger.error(f"Error al generar el reporte para nivel {nivel}: {e}")

            except Exception as e:
                logger.error(f"Error al procesar la aplicación {aplicacion.cve_aplic}: {e}")

    except Exception as e:
        logger.error(f"Error general en la tarea verificar_y_cerrar_aplicaciones: {e}")
