import os
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from dotenv import load_dotenv
from django.core.mail import send_mail
import logging
from django.core.signing import TimestampSigner, SignatureExpired, BadSignature
signer = TimestampSigner()
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from api.models import CustomUser
load_dotenv()

logger = logging.getLogger(__name__)
def enviar_correo_error(email, nivel, aplicacion, error_mensaje):
    """
    Envía un correo notificando que ocurrió un error al generar el reporte.

    Args:
        email: Correo electrónico del destinatario.
        nivel: Nivel para el que ocurrió el error.
        aplicacion: Aplicación en la que ocurrió el error.
        error_mensaje: Mensaje del error ocurrido.
    """
    email_host_user = os.environ.get('EMAIL_HOST_USER')
    if not email_host_user:
        logger.error("La variable de entorno 'EMAIL_HOST_USER' no está configurada.")
        return

    asunto = f"Error al generar el reporte para el nivel {nivel}"
    mensaje = (
        f"Hola,\n\n"
        f"Se produjo un error al generar el reporte para la aplicación {aplicacion.cve_aplic} "
        f"en el nivel {nivel}.\n\n"
        f"Detalles del error:\n{error_mensaje}\n\n"
        "Por favor, revise el sistema para obtener más detalles.\n\n"
        "Saludos,\nEl equipo."
    )

    try:
        send_mail(asunto, mensaje, email_host_user, [email])
        logger.info(f"Correo de error enviado a {email} para nivel {nivel}.")
    except Exception as e:
        logger.error(f"Error al enviar correo de error a {email}: {e}")
        
        
def enviar_notificacion_por_correo(usuario, nivel, aplicacion):
    """
    Envía un correo notificando la generación del reporte.
    """
    if not usuario or not hasattr(usuario, 'first_name') or not hasattr(usuario, 'email'):
        logger.error("El objeto 'usuario' no es válido.")
        return

    if not aplicacion or not hasattr(aplicacion, 'cve_aplic'):
        logger.error("El objeto 'aplicacion' no es válido.")
        return

    if not nivel:
        logger.error("El nivel proporcionado no es válido.")
        return

    asunto = f"Reporte generado para el nivel {nivel}"
    mensaje = (
        f"Hola {usuario.first_name},\n\n"
        f"Se ha generado un reporte para la aplicación {aplicacion.cve_aplic} "
        f"en el nivel {nivel}.\n\n"
        "Saludos,\nEl equipo."
    )

    try:
        email_host_user = os.environ.get('EMAIL_HOST_USER')
        if not email_host_user:
            logger.error("La variable de entorno 'EMAIL_HOST_USER' no está configurada.")
            return

        send_mail(asunto, mensaje, email_host_user, [usuario.email])
        logger.info("Correo enviado exitosamente.")
    except Exception as e:
        logger.error(f"Error al enviar el correo: {e}")
    

from django.http import JsonResponse

def activar_cuenta(request, token=None):
    """
    Activa la cuenta del usuario si el token es válido.
    """
    if request.method != "GET":
        return JsonResponse({"error": "Método no permitido."}, status=405)

    if not token:
        return JsonResponse({"error": "Token no proporcionado."}, status=400)

    try:
        user_id = signer.unsign(token, max_age=86400)# 1 día de duración
        user = get_object_or_404(CustomUser, pk=user_id)

        if user.is_active:
            return JsonResponse({"message": "Tu cuenta ya está activada. Por favor, inicia sesión."}, status=200)

        user.is_active = True
        user.save()
        return JsonResponse({"message": "Cuenta activada exitosamente. Ahora puedes iniciar sesión."}, status=200)
    except SignatureExpired:
        return JsonResponse({"error": "El enlace ha expirado. Por favor, solicita un nuevo enlace."}, status=400)
    except BadSignature:
        return JsonResponse({"error": "El enlace es inválido."}, status=400)

def enviar_correo_activacion(user):
    """
    Envía un correo al usuario con un enlace que apunta al frontend para activar su cuenta.
    """
    from django.core.signing import TimestampSigner
    signer = TimestampSigner()
    token = signer.sign(user.pk)

    # Dominio del frontend (en producción, cambia a tu dominio real)
    frontend_domain = settings.FRONTEND_DOMAIN #"http://localhost:3000"

    # Generar enlace para el frontend
    url = f"{frontend_domain}/activar?token={token}"

    asunto = "Activa tu cuenta"
    mensaje = (
        f"Hola {user.first_name},\n\n"
        "Gracias por registrarte. Por favor, activa tu cuenta haciendo clic en el siguiente enlace:\n\n"
        f"{url}\n\n"
        "Este enlace expirará en 1 dia.\n\n"
        "Saludos,\nEl equipo."
    )
    send_mail(asunto, mensaje, settings.EMAIL_HOST_USER, [user.email])