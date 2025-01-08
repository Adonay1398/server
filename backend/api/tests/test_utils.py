from django.test import TestCase
from unittest.mock import patch, Mock
from api.tasks import enviar_notificacion_por_correo
import os

class TestEnviarNotificacionPorCorreo(TestCase):

    @patch('django.core.mail.send_mail')  # Simula el envío de correo
    def test_enviar_notificacion_exitosamente(self, mock_send_mail):
        # Configurar variable de entorno simulada
        os.environ['EMAIL_HOST_USER'] = "prueba@example.com"
        
        # Simular objetos `usuario` y `aplicacion`
        usuario = Mock(first_name="Juan", email="le1908017@merida.tecnm.mx")
        aplicacion = Mock(cve_aplic="APP001")
        nivel = "Alto"
        
        # Llamar a la función
        enviar_notificacion_por_correo(usuario, nivel, aplicacion)
        
        # Verificar que se envió el correo con los parámetros correctos
        mock_send_mail.assert_called_once_with(
            "Reporte generado para el nivel Alto",
            "Hola Juan,\n\nSe ha generado un reporte para la aplicación APP001 en el nivel Alto.\n\nSaludos,\nEl equipo.",
            "prueba@example.com",
            ["juan@example.com"]
        )

    @patch('django.core.mail.send_mail')  # Simula el envío de correo
    def test_error_usuario_invalido(self, mock_send_mail):
        usuario = None  # Usuario inválido
        aplicacion = Mock(cve_aplic="APP001")
        nivel = "Alto"
        
        enviar_notificacion_por_correo(usuario, nivel, aplicacion)
        
        # Asegurarse de que no se intente enviar el correo
        mock_send_mail.assert_not_called()

    @patch('django.core.mail.send_mail')  # Simula el envío de correo
    def test_error_aplicacion_invalida(self, mock_send_mail):
        usuario = Mock(first_name="Juan", email="le1908017@merida.tecnm.mx")
        aplicacion = None  # Aplicación inválida
        nivel = "Alto"
        
        enviar_notificacion_por_correo(usuario, nivel, aplicacion)
        
        # Asegurarse de que no se intente enviar el correo
        mock_send_mail.assert_not_called()

    @patch('django.core.mail.send_mail')  # Simula el envío de correo
    def test_falta_variable_entorno(self, mock_send_mail):
        if 'EMAIL_HOST_USER' in os.environ:
            del os.environ['EMAIL_HOST_USER']  # Asegurarse de que no exista
        
        usuario = Mock(first_name="Juan", email="le1908017@merida.tecnm.mx")
        aplicacion = Mock(cve_aplic="APP001")
        nivel = "Alto"
        
        enviar_notificacion_por_correo(usuario, nivel, aplicacion)
        
        # Asegurarse de que no se intente enviar el correo
        mock_send_mail.assert_not_called()
