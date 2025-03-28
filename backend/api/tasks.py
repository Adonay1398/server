from django.http import HttpResponse
from celery import shared_task
from dotenv import load_dotenv

from api.modul.GenerateAnalysGroups import generar_reporte_individual_por_tutor, generar_reporte_por_grupo

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
    "departamento": [
        "coord.cea.dept@merida.tecnm.mx",
        "coord.ea.dept@conkal.tecnm.mx",
        "coord.sistemas.dept@merida.tecnm.mx",
    ],
    "institucion": [
        "coord.conkal.inst@conkal.tecnm.mx",
        "coord.merida.inst@merida.tecnm.mx",
    ],
    "nacion": ["coord.nacion@tecnm.mx"],
    "carrera": [
        "coord.ige.plan@merida.tecnm.mx",
        "coord.itic.plan@conkal.tecnm.mx",
        "coord.sistemas.plan@merida.tecnm.mx",
    ],
    "region": ["coord.region.sur@tecnm.mx"],
}

@shared_task
def verificar_y_cerrar_aplicaciones():
    """
    Tarea que verifica las aplicaciones cuya fecha límite ha pasado, las cierra automáticamente,
    y genera reportes para los niveles definidos en DEFAULT_EMAILS.
    """
    try:
        aplicaciones = DatosAplicacion.objects.all()
        if not aplicaciones.exists():
            logger.info("No hay aplicaciones para cerrar.")
            return

        usuarios = CustomUser.objects.filter(email__in=[email for emails in DEFAULT_EMAILS.values() for email in emails])
        usuarios_dict = {usuario.email: usuario for usuario in usuarios}
        
        for aplicacion in aplicaciones:
            try:
                if aplicacion.fecha_fin is not None and not aplicacion.reporte_generado:
                    logger.info(f"Aplicación cerrada: {aplicacion.cve_aplic}.")
                    cuestionarios = aplicacion.cuestionario.all()

                    if not cuestionarios.exists():
                        logger.warning(f"No cuestionarios asociados a la aplicación {aplicacion.cve_aplic}.")
                        continue
                    
                    for nivel, emails in DEFAULT_EMAILS.items():
                        for email in emails:
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

                    # Generar reportes individuales para usuarios asignados
                    usuarios_asignados = CustomUser.objects.filter(asignaciones__aplicacion=aplicacion).distinct()

                    for usuario in usuarios_asignados:
                        try:
                            logger.info(f"Generando reporte individual para usuario ID={usuario.id}.")
                            resultado = generar_reporte_individual_por_tutor(usuario, aplicacion, cuestionarios.first().cve_cuestionario)

                            if resultado["status"] == "success":
                                logger.info(f"Reporte individual generado para usuario ID={usuario.id}.")
                            else:
                                logger.warning(f"Error al generar reporte individual: {resultado['message']}")

                        except Exception as e:
                            logger.error(f"Error inesperado al generar reporte individual para usuario ID={usuario.id}: {e}")
                
                aplicacion.reporte_generado = True
                aplicacion.save()
                
            except Exception as e:
                logger.error(f"Error al procesar la aplicación {aplicacion.cve_aplic}: {e}")

        logger.info("Se generaron los reportes.")
    except Exception as e:
        logger.error(f"Error general en la tarea verificar_y_cerrar_aplicaciones: {e}")
    logger.info("Se terminó el proceso.")

""" @shared_task
def generar_reportes_aplicacion_task(aplicacion_id):
    
    Tarea para generar reportes de todos los usuarios asignados a una aplicación.
    
    from api.utils import generar_reportes_aplicacion
    resultado = generar_reportes_aplicacion(aplicacion_id)
    return resultado """