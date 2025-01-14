from collections import defaultdict
from datetime import datetime, time
from django import forms
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from marshmallow import ValidationError
from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated, DjangoModelPermissions, IsAdminUser
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication   
from rest_framework_simplejwt.views import TokenObtainPairView

from api.tasks import verificar_y_cerrar_aplicaciones


from .modul.GenerateAnalysGroups import generar_reporte_por_grupo
from .modul.analysis import calcular_scores
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import threading
from django.utils.timezone import now
from django.utils.timezone import make_aware
from .permissions import IsAuthorizedUser
from .models import *
from .serializers import *
#from .utils import calcular_scores_jerarquicos, calcular_scores_tutor
#from api.modul.retro_chatgpt_service import generar_retro_jerarquica, procesar_cuestionarios,calcular_scores_jerarquicos
#from api.utils import calcular_scores_jerarquicos #verificar_autenticacion_y_jerarquia
from .permissions import IsAuthorizedUser
from rest_framework.decorators import api_view
from django.core.signing import SignatureExpired, BadSignature,TimestampSigner

# ==========================
# USUARIOS
# ==========================

"""  """

class  CustomUserListView(generics.ListCreateAPIView):
    """
    Listar y crear usuarios.
    """
    queryset = CustomUser.objects.all()
    serializer_class = UserPersonalInfoSerializer
    permission_classes = [IsAuthenticated ]

class CustomUserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Obtener, actualizar o eliminar al usuario autenticado.
    """
    serializer_class = UserPersonalInfoSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """
        Retorna el usuario autenticado basado en el token.
        """
        return self.request.user
class CreateCooridnadorsView(generics.CreateAPIView):
    permission_classes= [AllowAny]
    queryset = CustomUser.objects.all()
    serializer_class = CoordinadoresRegistrationSerializer
    
    def post(self,request,*args, **kwargs):
        """
        Maneja solicitudes POST para crear un coordinador.
        """
        return super().post(request, *args, **kwargs)
    
class CreateTutorView(generics.CreateAPIView):
    """
    Crear un tutor.
    """
    
    permission_classes = [AllowAny]
    queryset = CustomUser.objects.all()
    serializer_class = TutorsRegistrationSerializer
    @swagger_auto_schema(
        operation_summary="Crear un tutor",
        operation_description=(
            "Este endpoint permite crear un nuevo tutor proporcionando los detalles requeridos. "
            "El cuerpo de la solicitud debe contener los campos necesarios para registrar un tutor."
        ),
        request_body=TutorsRegistrationSerializer,
        responses={
            201: openapi.Response(
                description="Tutor creado exitosamente.",
                examples={
                    "application/json": {
                        "id": 1,
                        "username": "tutor123",
                        "email": "tutor@example.com",
                        "first_name": "John",
                        "last_name": "Doe"

                    }
                }
            ),
            400: openapi.Response(
                description="Error en la solicitud.",
                examples={
                    "application/json": {
                        "error": "Los datos proporcionados no son válidos."
                    }
                }
            )
        }
    )
    def post(self, request, *args, **kwargs):
        """
        Maneja solicitudes POST para crear un tutor.

        Respuesta:
        - 201: Tutor creado exitosamente.
        - 400: Error en los datos proporcionados.
        """
        return super().post(request, *args, **kwargs)
    

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
# ==========================
# CONSTRUCTOS
# ==========================
class ConstructoListViews(generics.ListCreateAPIView):
    """
    Listar y crear constructos.
    """
    queryset = Constructo.objects.all()
    serializer_class = ConstructoSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]

class ConstructoDetailViews(generics.RetrieveUpdateDestroyAPIView):
    """
    Obtener, actualizar o eliminar un constructo.
    """
    queryset = Constructo.objects.all()
    serializer_class = ConstructoSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]

# ==========================
# SCORES (Constructos e Indicadores)
# ==========================
class ScoreConstructoListViews(generics.ListCreateAPIView):
    """
    Listar y crear scores de constructos.
    """
    queryset = ScoreConstructo.objects.all().select_related('usuario', 'constructo')
    serializer_class = ScoreConstructoSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]

class ScoreIndicadorListViews(generics.ListCreateAPIView):
    """
    Listar y crear scores de indicadores.
    """
    queryset = ScoreIndicador.objects.all().select_related('usuario', 'indicador')
    serializer_class = IndicadorScoreSerializer
    permission_classes = [IsAuthenticated]

# ==========================
# CUESTIONARIOS
# ==========================
class CuestionarioListView(generics.ListCreateAPIView):
    """
    Listar y crear cuestionarios.
    """
    queryset = Cuestionario.objects.all()
    serializer_class = CuestionarioSerializer
    permission_classes = [IsAuthenticated]

class CuestionarioStatusView(APIView):
    """
    Endpoint para obtener el estado de los cuestionarios relacionados con las aplicaciones asignadas.
    """
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_summary="Obtener estado de los cuestionarios",
        operation_description="Devuelve el estado de los cuestionarios relacionados con las aplicaciones asignadas al usuario autenticado.",
        responses={
            200: openapi.Response(
                description="Estados de los cuestionarios clasificados en 'on_hold' y 'submited'.",
                examples={
                    "application/json": {
                        "on_hold": {
                            "current": [
                                {
                                    "cve_cuestionario": 1,
                                    "nombre_corto": "Cuestionario 1",
                                    "is_active": True,
                                    "fecha_inicio": "2025-01-01",
                                    "fecha_fin": "2025-01-15",
                                    "fecha_limite": "2025-01-10",
                                    "is_past": False,
                                    "fecha_completado": None,
                                    "aplicaciones": [{"cve_aplic": 101}],
                                    "total_preguntas": 20,
                                    "preguntas_contestadas": 10
                                }
                            ],
                            "past": [
                                {
                                    "cve_cuestionario": 2,
                                    "nombre_corto": "Cuestionario 2",
                                    "is_active": False,
                                    "fecha_inicio": "2025-01-01",
                                    "fecha_fin": "2025-01-10",
                                    "fecha_limite": "2025-01-09",
                                    "is_past": True,
                                    "fecha_completado": None,
                                    "aplicaciones": [{"cve_aplic": 102}],
                                    "total_preguntas": 15,
                                    "preguntas_contestadas": 5
                                }
                            ]
                        },
                        "submited": [
                            {
                                "cve_cuestionario": 3,
                                "nombre_corto": "Cuestionario 3",
                                "is_active": True,
                                "fecha_inicio": "2025-01-01",
                                "fecha_fin": "2025-01-15",
                                "fecha_limite": "2025-01-14",
                                "is_past": False,
                                "fecha_completado": "2025-01-12",
                                "aplicaciones": [{"cve_aplic": 103}],
                                "total_preguntas": 10,
                                "preguntas_contestadas": 10
                            }
                        ]
                    }
                }
            ),
            404: openapi.Response(
                description="No se encontraron aplicaciones asignadas.",
                examples={
                    "application/json": {
                        "on_hold": {"current": [], "past": []},
                        "submited": []
                    }
                }
            ),
        }
    )
    def get(self, request, *args, **kwargs):
        user = request.user

        # Obtener las aplicaciones asignadas al usuario
        aplicaciones_asignadas = DatosAplicacion.objects.filter(asignaciones__usuario=user,fecha_inicion__lte=now().date()).distinct()

        if not aplicaciones_asignadas.exists():
            return Response({"on_hold": {"current": [], "past": []}, "submited": []}, status=200)

        on_hold_current = []
        on_hold_past = []
        submitted = []

        # Procesar cada aplicación asignada
        for aplicacion in aplicaciones_asignadas.prefetch_related('cuestionario__preguntas'):
            for cuestionario in aplicacion.cuestionario.all():
                # Contar el total de preguntas del cuestionario
                total_preguntas = cuestionario.preguntas.count()

                # Contar las preguntas contestadas por el usuario en la relación aplicación-cuestionario
                preguntas_contestadas = Respuesta.objects.filter(
                    user=user, 
                    pregunta__cuestionario=cuestionario, 
                    cve_aplic=aplicacion
                ).count()

                # Determinar si la aplicación es pasada o actual
                is_past = aplicacion.fecha_fin and aplicacion.fecha_fin < now().date()

                # Verificar si existe una asignación para esta combinación de aplicación y cuestionario
                asignacion = AsignacionCuestionario.objects.filter(
                    usuario=user, 
                    aplicacion=aplicacion, 
                    cuestionario=cuestionario
                ).first()

                # Crear el diccionario de datos de la aplicación-cuestionario
                aplicacion_cuestionario_data = {
                    "cve_aplic": aplicacion.cve_aplic,
                    #"nombre_aplicacion": aplicacion.nombre_aplicacion,
                    "cve_cuestionario": cuestionario.cve_cuestionario,
                    "nombre_cuestionario": cuestionario.nombre_corto,
                    "is_active": cuestionario.is_active,
                    "fecha_inicio": aplicacion.fecha_inicion,
                    "fecha_limite": aplicacion.fecha_limite,
                    "fecha_fin": aplicacion.fecha_fin.strftime("%Y-%m-%d") if aplicacion.fecha_fin else None,
                    "is_past": is_past,
                    "fecha_completado": asignacion.fecha_completado if asignacion else None,
                    "total_preguntas": total_preguntas,
                    "preguntas_contestadas": preguntas_contestadas,
                }

                # Clasificar en "submitted", "on_hold_current" o "on_hold_past"
                if preguntas_contestadas == total_preguntas:
                    submitted.append(aplicacion_cuestionario_data)
                elif is_past:
                    on_hold_past.append(aplicacion_cuestionario_data)
                else:
                    on_hold_current.append(aplicacion_cuestionario_data)

        return Response({
            "on_hold": {"current": on_hold_current, "past": on_hold_past},
            "submited": submitted
        }, status=200)


# ==========================
# RESPUESTAS
# ==========================
class StoreResponsesView(APIView):
    """
    Vista para almacenar respuestas de usuarios y calcular scores para constructos e indicadores.

    Esta clase maneja las solicitudes HTTP POST para guardar las respuestas de un usuario
    a un cuestionario específico dentro de una aplicación determinada. Además, puede
    calcular los scores asociados a constructos e indicadores basados en las respuestas almacenadas.

    Atributos:
        permission_classes (list): Lista de clases de permisos que determinan el acceso a la vista.
    """
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["cve_aplicacion", "cuestionario_id", "respuestas"],
            properties={
                "cve_aplicacion": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Clave de la aplicación."
                ),
                "cuestionario_id": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="ID del cuestionario."
                ),
                "respuestas": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    description="Lista de respuestas del cuestionario.",
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "cve_pregunta": openapi.Schema(
                                type=openapi.TYPE_STRING,
                                description="Clave de la pregunta."
                            ),
                            "respuesta": openapi.Schema(
                                type=openapi.TYPE_STRING,
                                description="Respuesta del usuario."
                            )
                        }
                    )
                ),
            }
        ),
        responses={
            200: openapi.Response(
                description="Respuestas almacenadas correctamente.",
                examples={
                    "application/json": {
                        "message": "Respuestas almacenadas."
                    }
                }
            ),
            404: openapi.Response(
                description="Aplicación o Cuestionario no encontrados.",
                examples={
                    "application/json": {
                        "error": "Aplicación no encontrada."
                    }
                }
            ),
            500: openapi.Response(
                description="Error interno del servidor.",
                examples={
                    "application/json": {
                        "error": "Error inesperado."
                    }
                }
            )
        }
    )
    def post(self, request, *args, **kwargs):
        """
        Maneja las solicitudes POST para almacenar respuestas de un usuario.

        Este método recibe los datos de las respuestas desde la solicitud, valida la existencia
        de la aplicación y el cuestionario, y luego guarda o actualiza cada respuesta en la base de datos.

        Args:
            request (Request): Objeto de solicitud que contiene los datos necesarios para almacenar las respuestas.
            *args: Argumentos adicionales.
            **kwargs: Argumentos de palabra clave adicionales.

        Returns:
            Response: Respuesta HTTP con un mensaje de éxito y código de estado 200 si todo se procesa correctamente,
                    o con mensajes de error y códigos de estado apropiados en caso de fallos.
        """
        user = request.user
        cve_aplicacion = request.data.get('cve_aplicacion')
        cuestionario_id = request.data.get('cuestionario_id')
        respuestas = request.data.get('respuestas')

        try:
            aplicacion = DatosAplicacion.objects.get(pk=cve_aplicacion)
            cuestionario = Cuestionario.objects.get(pk=cuestionario_id)

            for respuesta in respuestas:
                cve_pregunta = str(respuesta['cve_pregunta'])
                valor = respuesta['respuesta']
                pregunta = Pregunta.objects.get(cve_pregunta=cve_pregunta)
                Respuesta.objects.update_or_create(
                    user=user,
                    pregunta=pregunta,
                    cve_aplic=aplicacion,
                    defaults={'valor': valor}
                )

            return Response({"message": "Respuestas almacenadas."}, status=status.HTTP_200_OK)

        except DatosAplicacion.DoesNotExist:
            return Response({"error": "Aplicación no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        except Cuestionario.DoesNotExist:
            return Response({"error": "Cuestionario no encontrado."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ==========================
# AGREGADOS

# ==========================


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.exceptions import ValidationError
from .models import RetroChatGPT

class UserRelatedDataRetroView(APIView):
    """
    Vista para obtener datos relacionados con el usuario y un cuestionario específico.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Obtener datos relacionados con el usuario y un cuestionario",
        operation_description=(
            "Este endpoint devuelve datos relacionados con el usuario autenticado, "
            "un cuestionario específico (`Cuestionario_id`) y una aplicación (`aplicacion_id`)."
        ),
        manual_parameters=[
            openapi.Parameter(
                "Cuestionario_id", openapi.IN_PATH,
                description="ID del cuestionario relacionado.",
                type=openapi.TYPE_INTEGER,
                required=True
            ),
            openapi.Parameter(
                "aplicacion_id", openapi.IN_PATH,
                description="ID de la aplicación relacionada.",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Datos relacionados con el usuario y el cuestionario.",
                examples={
                    "application/json": {
                        "id": 42,
                        "username": "johndoe",
                        "email": "johndoe@example.com",
                        "related_data": {
                            "cuestionario_id": 10,
                            "aplicacion_id": 101,
                            "other_field": "value"
                        }
                    }
                }
            ),
            401: openapi.Response(
                description="No autorizado.",
                examples={
                    "application/json": {
                        "detail": "Credenciales no válidas."
                    }
                }
            )
        }
    )
    def get(self, request, Cuestionario_id, aplicacion_id, *args, **kwargs):
        """
        Maneja solicitudes GET para obtener datos relacionados con el usuario y un cuestionario específico.

        Parámetros:
        - `Cuestionario_id` (int): ID del cuestionario relacionado.
        - `aplicacion_id` (int): ID de la aplicación relacionada.

        Respuesta:
        - 200: Datos obtenidos exitosamente.
        - 401: No autorizado.
        """
        user = request.user

        # Validar parámetros
        if not Cuestionario_id:
            return Response({"error": "El parámetro 'Cuestionario_id' es obligatorio."}, status=status.HTTP_400_BAD_REQUEST)

        if not aplicacion_id:
            return Response({"error": "El parámetro 'aplicacion_id' es obligatorio."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            retroalimentaciones = RetroChatGPT.objects.filter(
                usuario=user,
                Cuestionario_id=Cuestionario_id,
                aplicacion_id=aplicacion_id
            ).last()

            if not retroalimentaciones:
                return Response({"error": "No se encontraron retroalimentaciones para este cuestionario y aplicación."}, status=status.HTTP_404_NOT_FOUND)

            # Construir la respuesta
            respuesta = {
                "fortaleza": retroalimentaciones.texto1 if retroalimentaciones.texto1 else None,
                "oportunidad": retroalimentaciones.texto2 if retroalimentaciones.texto2 else None
            }
            return Response(respuesta, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserDataReporteView(APIView):
    """
    Vista para obtener información relacionada con el usuario autenticado.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        responses={
            200: openapi.Response(
                description="Información relacionada al usuario autenticado.",
                schema=UserRelatedDataReporteSerializer
            ),
            401: openapi.Response(
                description="Usuario no autenticado.",
                examples={
                    "application/json": {
                        "detail": "No se enviaron credenciales de autenticación."
                    }
                }
            )
        }
    )
    def get(self, request, *args, **kwargs):
        """
        Retorna la información relacionada al usuario autenticado.
        """
        # Obtener el ID del cuestionario desde los query params
        """ cuestionario_id = request.data.get('cuestionario_id')
        print(cuestionario_id)  # Verifica los parámetros enviados en la solicitud

        if not cuestionario_id:
            return Response(
                {"error": "Debe proporcionar un ID de cuestionario válido."},
                status=status.HTTP_400_BAD_REQUEST
            ) """

        # Pasar el ID del cuestionario al serializador a través del contexto
        serializer = UserRelatedDataReporteSerializer(
            request.user,
            context={"request": request, "cuestionario_id": cuestionario_id}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


        


class ResponderPreguntaView(APIView):
    

    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_summary="Guardar respuesta a una pregunta",
        operation_description=(
            "Este endpoint permite guardar la respuesta de un usuario a una pregunta específica en un cuestionario. "
            "Si todas las preguntas han sido contestadas, se calcula automáticamente el score."
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["id_pregunta", "respuesta", "cve_aplic"],
            properties={
                "id_pregunta": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="ID único de la pregunta a responder."
                ),
                "respuesta": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="El índice de la respuesta seleccionada, basado en el scorekey de la pregunta."
                ),
                "cve_aplic": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="Clave única de la aplicación del cuestionario."
                ),
            },
        ),
        responses={
            201: openapi.Response(
                description="Respuesta guardada exitosamente.",
                examples={
                    "application/json": {
                        "mensaje": "Respuesta guardada exitosamente.",
                        "respuesta": {
                            "id_pregunta": 1,
                            "respuesta": 5,
                            "cve_aplic": 101,
                            "usuario": 1001
                        }
                    }
                }
            ),
            400: openapi.Response(
                description="Solicitud inválida.",
                examples={
                    "application/json": {
                        "error": "Índice de respuesta fuera de rango para scorekey."
                    }
                }
            ),
            403: openapi.Response(
                description="Acceso denegado.",
                examples={
                    "application/json": {
                        "error": "No tiene acceso a esta aplicación."
                    }
                }
            ),
            404: openapi.Response(
                description="No se encontró la pregunta o aplicación.",
                examples={
                    "application/json": {
                        "error": "Pregunta no encontrada."
                    }
                }
            ),
            500: openapi.Response(
                description="Error interno del servidor.",
                examples={
                    "application/json": {
                        "error": "Error inesperado al procesar la solicitud."
                    }
                }
            ),
        },
    )
    def post(self, request, *args, **kwargs):

        # Extraer datos del cuerpo de la solicitud
        id_pregunta = request.data.get("id_pregunta")  # Este será el cve_pregunta enviado desde el cliente
        respuesta_valor = request.data.get("respuesta")
        cve_aplic = request.data.get("cve_aplic")
        user = request.user

        # Verificar si la aplicación está asignada al usuario
        if not DatosAplicacion.objects.filter(cve_aplic=cve_aplic, asignaciones__usuario=user).exists():
            return Response({"error": "No tiene acceso a esta aplicación."}, status=403)

        if not id_pregunta or not respuesta_valor or not cve_aplic:
            return Response(
                {"error": "Los campos 'id_pregunta', 'respuesta' y 'cve_aplic' son obligatorios."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            aplicacion = DatosAplicacion.objects.get(cve_aplic=cve_aplic)
            pregunta = Pregunta.objects.get(id_pregunta=id_pregunta)  # Cam
            
            # Calcular el índice basado en la respuesta
            index = int(respuesta_valor) - 1  # Restar 1 para convertir a índice de base 0
            if index < 0 or index >= len(pregunta.scorekey):
                return Response({"error": "Índice de respuesta fuera de rango para scorekey."}, status=400)
            print("index:",index)

            # Obtener el valor del scorekey en el índice correspondiente
            score_value = pregunta.scorekey[index]
            # Crear o actualizar la respuesta asociada al usuario autenticado
            print("valor score:",score_value)
            respuesta, created = Respuesta.objects.update_or_create(
                user=request.user,
                pregunta=pregunta,
                cve_aplic=aplicacion,
                defaults={"valor": score_value},
            )
            total_preguntas = Pregunta.objects.filter(cuestionario=pregunta.cuestionario).count()
            preguntas_contestadas = Respuesta.objects.filter(
                user=user, 
                cve_aplic=aplicacion, 
                pregunta__cuestionario=pregunta.cuestionario
            ).count()
            if preguntas_contestadas == total_preguntas:
                # Si se han contestado todas las preguntas, calcular scores
                asignacion = AsignacionCuestionario.objects.get(
                    usuario=user, cuestionario=pregunta.cuestionario, aplicacion=aplicacion
                )
                asignacion.completado = True 
                asignacion.fecha_completado = datetime.now().date() 
                asignacion.save()
                thread = threading.Thread(target=calcular_scores, args= (user, aplicacion,pregunta.cuestionario))
                thread.start()
                print("ok")
                return Response({"message": "Respuesta guardada y scores calculados."}, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
            # Construir la respuesta de éxito
            response_data = {
                "mensaje": "Respuesta guardada exitosamente.",
                "respuesta": {
                    "id_pregunta": respuesta.pregunta.id_pregunta,
                    "respuesta": respuesta.valor,   
                    "cve_aplic": aplicacion.cve_aplic,
                    "usuario": request.user.id,
                },
            }
            return Response(response_data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

        except DatosAplicacion.DoesNotExist:
            return Response({"error": "Aplicación no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        except Pregunta.DoesNotExist:
            return Response({"error": "Pregunta no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PreguntaView(APIView):
    """
    Vista para manejar solicitudes relacionadas con las preguntas de un cuestionario.
    """
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_summary="Obtener preguntas pendientes de un cuestionario",
        operation_description=(
            "Este endpoint devuelve las preguntas pendientes de un cuestionario para el usuario autenticado. "
            "Requiere proporcionar el ID del cuestionario (`cuestionario`) y la ID de la aplicación (`aplicacion`) "
            "a través de los parámetros de consulta."
        ),
        manual_parameters=[
            openapi.Parameter(
                "cuestionario", openapi.IN_QUERY,
                description="ID del cuestionario.",
                type=openapi.TYPE_INTEGER,
                required=True
            ),
            openapi.Parameter(
                "aplicacion", openapi.IN_QUERY,
                description="ID de la aplicación.",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Lista de preguntas pendientes y observaciones de la aplicación.",
                examples={
                    "application/json": {
                        "Observaciones": "Observaciones sobre la aplicación.",
                        "preguntas": [
                            {"numero": 1, "id_pregunta": 101, "texto_pregunta": "¿Cuál es tu color favorito?"},
                            {"numero": 2, "id_pregunta": 102, "texto_pregunta": "¿Te gusta la música clásica?"}
                        ]
                    }
                }
            ),
            400: openapi.Response(
                description="Faltan parámetros requeridos.",
                examples={
                    "application/json": {
                        "error": "Debe proporcionar el ID del cuestionario y la aplicación."
                    }
                }
            ),
            403: openapi.Response(
                description="El usuario no tiene acceso a la aplicación.",
                examples={
                    "application/json": {
                        "error": "No tiene acceso a esta aplicación."
                    }
                }
            ),
            404: openapi.Response(
                description="No se encontró la aplicación o el cuestionario.",
                examples={
                    "application/json": {
                        "error": "No encontrado."
                    }
                }
            )
        }
    )
    def get(self, request, *args, **kwargs):
        cuestionario_id = request.query_params.get("cuestionario")
        aplicacion_id = request.query_params.get("aplicacion")

        if not cuestionario_id or not aplicacion_id:
            return Response({"error": "Debe proporcionar el ID del cuestionario y la aplicación."}, status=400)

        user = request.user

        # Verificar si la aplicación está asignada al usuario
        if not DatosAplicacion.objects.filter(cve_aplic=aplicacion_id, asignaciones__usuario=user).exists():
            return Response({"error": "No tiene acceso a esta aplicación."}, status=403)

        # Obtener las preguntas ya contestadas
        preguntas_contestadas = Respuesta.objects.filter(
            user=user,
            cve_aplic_id=aplicacion_id,
            pregunta__cuestionario_id=cuestionario_id
        ).values_list('pregunta__id_pregunta', flat=True)

        # Obtener preguntas pendientes
        preguntas_pendientes = Pregunta.objects.filter(
            cuestionario_id=cuestionario_id
        ).exclude(id_pregunta__in=preguntas_contestadas)

        # Calcular el número de inicio basado en las preguntas ya contestadas
        numero_inicio = len(preguntas_contestadas) + 1

        # Formatear las preguntas pendientes con número e ID
        data = [
            
            {
                "numero": idx + numero_inicio,
                "id_pregunta": pregunta.id_pregunta,
                "texto_pregunta": pregunta.texto_pregunta,
            }
            for idx, pregunta in enumerate(preguntas_pendientes)
        ]
        aplicacion = get_object_or_404(DatosAplicacion, cve_aplic=aplicacion_id)

        return Response({"Observaciones":aplicacion.observaciones, "preguntas": data}, status=200)




class AsignarCuestionarioGrupoView(APIView):
    
    permission_classes = [AllowAny]
    @swagger_auto_schema(
        operation_summary="Asignar la aplicaciond de uno o mas cuestionarios a un grupo",
        operation_description=(
            "Este endpoint asigna uno o mas cuestionarios específico a todos los usuarios de un grupo. "
            "Requiere proporcionar  el ID del grupo, y el ID de la aplicación."
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=[ "grupo", "aplicacion"],
            properties={
                
                "grupo": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="ID del grupo al que se desea asignar el cuestionario."
                ),
                "aplicacion": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="ID de la aplicación del cuestionario."
                ),
            },
        ),
        responses={
            200: openapi.Response(
                description="aplicacion asignado exitosamente.",
                examples={
                    "application/json": {
                        "message": "aplicacion asignado exitosamente al grupo"
                    }
                }
            ),
            400: openapi.Response(
                description="Solicitud inválida.",
                examples={
                    "application/json": {
                        "error": "Debe proporcionar , grupo y aplicación"
                    }
                }
            ),
            404: openapi.Response(
                description="No se encontró el  grupo o aplicación.",
                examples={
                    "application/json": {
                        "error": "Cuestionario no encontrado"
                    }
                }
            ),
            500: openapi.Response(
                description="Error interno del servidor.",
                examples={
                    "application/json": {
                        "error": "Error inesperado al procesar la solicitud."
                    }
                }
            ),
        },
    )
    def post(self, request, *args, **kwargs):
        #cuestionario_id = request.data.get('cuestionario', None)
        grupo_id = request.data.get('grupo', None)
        aplicacion_id = request.data.get('aplicacion', None)

        """ if not cuestionario_id or not grupo_id or not aplicacion_id:
            return Response({"error": "Debe proporcionar cuestionario, grupo y aplicación"}, status=status.HTTP_400_BAD_REQUEST)
        """
        try:
            # Obtener grupo, aplicación y cuestionarios
            grupo = Group.objects.get(pk=grupo_id)
            aplicacion = DatosAplicacion.objects.get(pk=aplicacion_id)
            
            # Obtener todos los cuestionarios asociados a la aplicación
            cuestionarios = aplicacion.cuestionario.all()  # Obtiene todos los cuestionarios

            if not cuestionarios.exists():
                return Response({"error": "No se encontraron cuestionarios para esta aplicación"}, status=status.HTTP_404_NOT_FOUND)

            # Obtener los usuarios que pertenecen al grupo
            usuarios = CustomUser.objects.filter(groups=grupo)

            # Asignar todos los cuestionarios a cada usuario del grupo
            for usuario in usuarios:
                for cuestionario in cuestionarios:
                    AsignacionCuestionario.objects.get_or_create(
                        usuario=usuario,
                        cuestionario=cuestionario,
                        aplicacion=aplicacion
                    )
            return Response({"message": "Aplicacion de cuestionario asignado exitosamente al grupo"}, status=status.HTTP_200_OK)

        
        except Group.DoesNotExist:
            return Response({"error": "Grupo no encontrado"}, status=status.HTTP_404_NOT_FOUND)
        except DatosAplicacion.DoesNotExist:
            return Response({"error": "Aplicación no encontrada"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AsignarCuestionarioUsuarioView(APIView):
    
    permission_classes = [AllowAny]
    @swagger_auto_schema(
        operation_summary="Asignar una aplicacion de un o mas cuestionarios a usuario",
        operation_description=(
            "Este endpoint asigna una aplicacion de uno o mas cuestionarios   a un usuario dentro de una aplicación específica. "
            "Se debe proporcionar  el ID del usuario y la clave de la aplicación (`cve_aplic`)."
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=[ "usuario", "cve_aplic"],
            properties={
                
                "usuario": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="ID del usuario al que se asignará el cuestionario."
                ),
                "cve_aplic": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="Clave única de la aplicación asociada."
                )
            }
        ),
        responses={
            200: openapi.Response(
                description="aplicacion de Cuestionario asignado exitosamente al usuario.",
                examples={
                    "application/json": {
                        "message": "aplicacion de Cuestionario asignado exitosamente al usuario"
                    }
                }
            ),
            400: openapi.Response(
                description="Faltan parámetros obligatorios o son inválidos.",
                examples={
                    "application/json": {
                        "error": "Debe proporcionar  usuario y aplicación"
                    }
                }
            ),
            404: openapi.Response(
                description="No se encontró uno de los recursos especificados.",
                examples={
                    "application/json": {
                        "error": "aplicacion de Cuestionario no encontrado"
                    }
                }
            ),
            500: openapi.Response(
                description="Error interno del servidor.",
                examples={
                    "application/json": {
                        "error": "Descripción del error interno."
                    }
                }
            )
        }
    )
    def post(self, request, *args, **kwargs):
        #cuestionario_id = request.data.get('cuestionario', None)
        usuario_id = request.data.get('usuario', None)
        aplicacion_id = request.data.get('cve_aplic', None)
        
        """  print(cuestionario_id, usuario_id, aplicacion_id)
        if not cuestionario_id or not usuario_id or not aplicacion_id:
            return Response({"error": "Debe proporcionar cuestionario, usuario y aplicación"}, status=status.HTTP_400_BAD_REQUEST)
        """
        try:
        # Obtener usuario, aplicación y cuestionarios
            usuario = CustomUser.objects.get(pk=usuario_id)
            aplicacion = DatosAplicacion.objects.get(pk=aplicacion_id)
            cuestionarios = aplicacion.cuestionario.all()  # Obtener todos los cuestionarios asociados

            if not cuestionarios.exists():
                return Response({"error": "No se encontraron cuestionarios para esta aplicación"}, status=status.HTTP_404_NOT_FOUND)

            # Asignar todos los cuestionarios al usuario
            for cuestionario in cuestionarios:
                AsignacionCuestionario.objects.get_or_create(
                    usuario=usuario,
                    cuestionario=cuestionario,
                    aplicacion=aplicacion
                )

            return Response({"message": "Aplicacion de Cuestionario asignado exitosamente al usuario"}, status=status.HTTP_200_OK)

        except CustomUser.DoesNotExist:
            return Response({"error": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND)
        except DatosAplicacion.DoesNotExist:
            return Response({"error": "Aplicación no encontrada"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


class ListarReportesAPIView(APIView):
    """
    Endpoint para listar los reportes de un usuario.
    """

    def get(self, request):
        usuario = request.user
        reportes = RetroChatGPT.objects.filter(usuario=usuario).order_by('-creado_en')
        serializer = RetroChatGPTSerializer(reportes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    



"""         
class NavegarNivelesAPIView(APIView):
    
    Endpoint para navegar entre niveles jerárquicos.
    
    def get(self, request, *args, **kwargs):
        # Obtener parámetros de la consulta
        nivel = request.query_params.get('nivel')
        id_actual = request.query_params.get('id')

        if not nivel:
            return Response({"error": "El parámetro 'nivel' es obligatorio."}, status=400)

        # Consultar y devolver el nivel inferior según el nivel actual
        if nivel == "region":
            regiones = Region.objects.all()
            if id_actual:
                institutos = Instituto.objects.filter(region_id=id_actual)
                return Response({"nivel": "instituto", "datos": [{"id": i.cve_inst, "nombre": i.nombre_completo} for i in institutos]})
            return Response({"nivel": "region", "datos": [{"id": r.cve_region, "nombre": r.nombre} for r in regiones]})

        elif nivel == "instituto":
            institutos = Instituto.objects.all()
            if id_actual:
                departamentos = Departamento.objects.filter(instituto_id=id_actual)
                return Response({"nivel": "departamento", "datos": [{"id": d.cve_depto, "nombre": d.nombre} for d in departamentos]})
            return Response({"nivel": "instituto", "datos": [{"id": i.cve_inst, "nombre": i.nombre_completo} for i in institutos]})

        elif nivel == "departamento":
            departamentos = Departamento.objects.all()
            if id_actual:
                carreras = Carrera.objects.filter(departamento_id=id_actual)
                return Response({"nivel": "carrera", "datos": [{"id": c.cve_carrera, "nombre": c.nombre} for c in carreras]})
            return Response({"nivel": "departamento", "datos": [{"id": d.cve_depto, "nombre": d.nombre} for d in departamentos]})

        elif nivel == "carrera":
            carreras = Carrera.objects.all()
            return Response({"nivel": "carrera", "datos": [{"id": c.cve_carrera, "nombre": c.nombre} for c in carreras]})

        else:
            return Response({"error": f"Nivel '{nivel}' no válido."}, status=400)

 """
class InstitutoCarrerasView(APIView):
    """
    Endpoint para devolver la lista de institutos con solo el nombre y sus carreras.
    """
    permission_classes = [AllowAny]  # Opcional, si necesitas autenticación
    @swagger_auto_schema(
        operation_summary="Listar institutos y carreras",
        operation_description="Este endpoint devuelve una lista de todos los institutos junto con sus respectivas carreras.",
        responses={
            200: openapi.Response(
                description="Lista de institutos y carreras recuperada exitosamente.",
                examples={
                    "application/json": [
                        {
                            "id": 1,
                            "nombre": "Instituto Tecnológico A",
                            "carreras": [
                                {"id": 1, "nombre": "Ingeniería en Sistemas"},
                                {"id": 2, "nombre": "Ingeniería Civil"}
                            ]
                        },
                        {
                            "id": 2,
                            "nombre": "Instituto Tecnológico B",
                            "carreras": [
                                {"id": 3, "nombre": "Ingeniería Mecánica"},
                                {"id": 4, "nombre": "Ingeniería Eléctrica"}
                            ]
                        }
                    ]
                }
            ),
            500: openapi.Response(
                description="Error interno del servidor.",
                examples={
                    "application/json": {
                        "error": "Error al recuperar los institutos."
                    }
                }
            ),
        }
    )
    def get(self, request, *args, **kwargs):
        institutos = Instituto.objects.all()
        serializer = InstitutoSerializer(institutos, many=True)
        return Response(serializer.data, status=200)
    
class CascadeUploadView(APIView):
    """
    Vista para registrar o actualizar Región, Instituto, Departamento y Carrera por campos planos.
    """
    

    @swagger_auto_schema(
        operation_summary="Registrar o actualizar cascada de datos jerárquicos",
        operation_description=(
            "Este endpoint permite registrar o actualizar una región, instituto, "
            "departamento y carrera en un solo llamado utilizando campos planos."
        ),
        request_body= CascadeUploadSerializer,
        responses={
            200: openapi.Response(
                description="Registros actualizados o creados con éxito.",
                examples={
                    "application/json": {
                        "message": "Registros actualizados o creados con éxito.",
                        "region": {"id": 1, "nombre": "Región Norte"},
                        "instituto": {"id": 10, "nombre_completo": "Instituto Tecnológico X"},
                        "departamento": {"id": 20, "nombre": "Departamento de Ciencias Básicas"},
                        "carrera": {"id": 30, "nombre": "Ingeniería en Sistemas Computacionales"}
                    }
                }
            ),
            400: openapi.Response(
                description="Error de validación en los datos enviados.",
                examples={
                    "application/json": {
                        "region_nombre": ["Este campo es obligatorio."],
                        "instituto_nombre": ["Este campo es obligatorio."]
                    }
                }
            ),
            500: openapi.Response(
                description="Error interno del servidor.",
                examples={
                    "application/json": {
                        "error": "Descripción del error interno."
                    }
                }
            )
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = CascadeUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Datos validados
        region_nombre = serializer.validated_data['region_nombre']
        instituto_nombre = serializer.validated_data['instituto_nombre']
        departamento_nombre = serializer.validated_data['departamento_nombre']
        carrera_nombre = serializer.validated_data['carrera_nombre']

        try:
            # Crear o actualizar la región
            region, _ = Region.objects.update_or_create(nombre=region_nombre)

            # Crear o actualizar el instituto
            instituto, _ = Instituto.objects.update_or_create(
                nombre_completo=instituto_nombre,
                defaults={"region": region}
            )

            # Crear o actualizar el departamento
            departamento, _ = Departamento.objects.update_or_create(
                nombre=departamento_nombre,
                defaults={"instituto": instituto}
            )

            # Crear o actualizar la carrera
            carrera, _ = Carrera.objects.update_or_create(
                nombre=carrera_nombre,
                defaults={"departamento": departamento}
            )

            return Response({
                "message": "Registros actualizados o creados con éxito.",
                "region": {"id": region.cve_region, "nombre": region.nombre},
                "instituto": {"id": instituto.cve_inst, "nombre_completo": instituto.nombre_completo},
                "departamento": {"id": departamento.cve_depto, "nombre": departamento.nombre},
                "carrera": {"id": carrera.cve_carrera, "nombre": carrera.nombre},
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class CerrarAplicacionCuestionarioView(APIView):
    """
    Endpoint para cerrar una aplicación de un cuestionario.
    """
    #permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_summary="Cerrar una aplicación de cuestionario",
        operation_description=(
            "Este endpoint cierra una aplicación de cuestionario especificando su clave única (`cve_aplic`). "
            "Además, genera un reporte en segundo plano."
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["cve_aplic"],
            properties={
                "cve_aplic": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="Clave única de la aplicación que se desea cerrar."
                ),
                "Cuestionario_id": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="ID del cuestionario asociado a la aplicación."
                )
            }
        ),
        responses={
            200: openapi.Response(
                description="La aplicación fue cerrada exitosamente.",
                examples={
                    "application/json": {
                        "message": "La aplicación con clave 123 ha sido cerrada exitosamente.",
                        "fecha_cierre": "2025-01-02"
                    }
                }
            ),
            400: openapi.Response(
                description="Solicitud incorrecta.",
                examples={
                    "application/json": {
                        "error": "El campo 'cve_aplic' es obligatorio."
                    }
                }
            ),
            404: openapi.Response(
                description="Aplicación no encontrada.",
                examples={
                    "application/json": {
                        "error": "Aplicación no encontrada."
                    }
                }
            ),
            500: openapi.Response(
                description="Error interno del servidor.",
                examples={
                    "application/json": {
                        "error": "Descripción detallada del error interno."
                    }
                }
            )
        }
    )
    def post(self, request, *args, **kwargs):
        """
        Maneja solicitudes POST para cerrar una aplicación de un cuestionario.

        Parámetros:
        - cve_aplic (int): Clave de la aplicación que se desea cerrar.

        Respuesta:
        - 200: Aplicación cerrada exitosamente.
        - 404: Aplicación no encontrada.
        - 400: La aplicación ya está cerrada o no se puede cerrar.
        """
        cve_aplic = request.data.get('cve_aplic')
        #Cuestionario_id = request.data.get('Cuestionario_id')
        if not cve_aplic:
            return Response({"error": "El campo 'cve_aplic' es obligatorio."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Buscar la aplicación
            aplicacion = DatosAplicacion.objects.get(cve_aplic=cve_aplic)
            # Asumiendo que la relación es ForeignKey
            # Verificar si la aplicación ya está cerrada
            if aplicacion.fecha_fin and aplicacion.fecha_fin <= now().date():
                return Response({"error": "La aplicación ya está cerrada."}, status=status.HTTP_400_BAD_REQUEST)

            # Marcar la aplicación como cerrada
            aplicacion.fecha_fin = now().date()
            aplicacion.save()
            #theread = threading.Thread(target=generar_reporte_por_grupo, args=(request.user, aplicacion, Cuestionario_id))
            #theread.start()
            #generar_reportes_aplicacion_task.delay(aplicacion.cve_aplic)
            theread = threading.Thread(target=verificar_y_cerrar_aplicaciones)
            theread.start()
            #thearead = verificar_y_cerrar_aplicaciones()
            return Response(
                {
                    "message": f"La aplicación con clave {cve_aplic} ha sido cerrada exitosamente.",
                    "fecha_cierre": aplicacion.fecha_fin
                },
                status=status.HTTP_200_OK
            )

        except DatosAplicacion.DoesNotExist:
            return Response({"error": "Aplicación no encontrada."}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class RelacionCuestionarioAplicacionView(APIView):
    """
    Endpoint para gestionar la relación entre aplicaciones y cuestionarios.
    """
    @swagger_auto_schema(
        operation_summary="Crear relación entre aplicación y cuestionario",
        operation_description="Este endpoint crea una relación entre una aplicación y un cuestionario.",
        request_body=RelacionCuestionarioAplicacionSerializer,
        responses={
            201: openapi.Response(
                description="Relación creada exitosamente.",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Relación creada exitosamente."
                    }
                }
            ),
            400: "Datos inválidos. Por favor, verifique los errores."
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = RelacionCuestionarioAplicacionSerializer(data=request.data)
        if serializer.is_valid():
            result = serializer.create(serializer.validated_data)
            return Response(result, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        serializer = RelacionCuestionarioAplicacionSerializer(data=request.data)
        if serializer.is_valid():
            result = serializer.delete(serializer.validated_data)
            return Response(result, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ListarAplicacionesView(APIView):
    """
    Endpoint para listar todas las aplicaciones activas y pasadas.
    """
    
    permission_classes = [IsAuthorizedUser]

    @swagger_auto_schema(
        operation_summary="Listar aplicaciones activas y pasadas",
        operation_description=(
            "Este endpoint permite obtener una lista de aplicaciones activas (con fecha límite mayor o igual "
            "a la fecha actual y aún no finalizadas) y aplicaciones pasadas (que ya han finalizado)."
        ),
        responses={
            200: openapi.Response(
                description="Lista de aplicaciones activas y pasadas",
                examples={
                    "application/json": {
                        "activas": [
                            {
                                "nombre_aplicacion": "Aplicación 1",
                                "cve_aplic": 1,
                                "fecha_inicio": "2025-01-01",
                                "fecha_limite": "2025-01-10",
                                "cuestionarios": ["Cuestionario 1", "Cuestionario 2"],
                                "observaciones": "Aplicación activa actualmente."
                            }
                        ],
                        "pasadas": [
                            {
                                "nombre_aplicacion": "Aplicación 2",
                                "cve_aplic": 2,
                                "fecha_inicio": "2024-12-01",
                                "fecha_fin": "2024-12-31",
                                "cuestionarios": ["Cuestionario 3"],
                                "observaciones": "Aplicación completada."
                            }
                        ]
                    }
                },
            ),
            500: openapi.Response(
                description="Error interno del servidor",
                examples={
                    "application/json": {
                        "error": "Descripción del error"
                    }
                }
            )
        }
    )
    def get(self, request, *args, **kwargs):
        try:
            # Filtrar todas las aplicaciones
            aplicaciones = DatosAplicacion.objects.all()

            # Serializar los datos
            data = {
                "aplicaciones": [
                    {
                        "nombre_aplicacion": aplicacion.nombre_aplicacion,
                        "cve_aplic": aplicacion.cve_aplic,
                        "fecha_inicio": aplicacion.fecha_inicion,
                        "fecha_limite": aplicacion.fecha_limite,
                        "fecha_fin": aplicacion.fecha_fin,
                        "cuestionarios": [cuestionario.nombre_corto for cuestionario in aplicacion.cuestionario.all()],
                        "observaciones": aplicacion.observaciones,
                        
                        "activo": (
                            True if (aplicacion.fecha_fin is None and (aplicacion.fecha_limite is None or aplicacion.fecha_limite >= now().date())) else False
                        )
                    }
                    for aplicacion in aplicaciones
                ]
            }

            return Response(data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        

#@api_view(['POST'])
class crear_aplicacionView(APIView):
    """
    Vista para crear una aplicación.
    """
    permission_classes = [IsAdminUser]
    @swagger_auto_schema(
        operation_summary="Crear una nueva aplicación",
        operation_description="Este endpoint permite crear una nueva aplicación y asignar cuestionarios.",
        request_body=DatosAplicacionSerializer,
        responses={
            201: openapi.Response(
                description="Aplicación creada exitosamente",
                examples={
                    "application/json": {
                        "message": "Aplicación creada y cuestionarios asignados",
                        "data": {
                            "nombre_aplicacion": "Nueva Aplicación",
                            "fecha_inicio": "2025-01-01",
                            "fecha_limite": "2025-01-10",
                            "cuestionarios": [1, 2],
                            "observaciones": "Aplicación activa"
                        }
                    }
                },
            ),
            400: openapi.Response(
                description="Errores de validación",
                examples={
                    "application/json": {
                        "nombre_aplicacion": ["Este campo es obligatorio."],
                        "cuestionarios": ["Debe proporcionar al menos un cuestionario."]
                    }
                },
            ),
        }
    )
    def post(self, request, *args, **kwargs):
        if request.method == 'POST':
            serializer = DatosAplicacionSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "message": "Aplicación creada y cuestionarios asignados",
                    "data": serializer.data
                }, status=status.HTTP_201_CREATED)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        

signer = TimestampSigner()

class ActivarCuentaView(APIView):
    """
    API para activar la cuenta del usuario mediante un token.
    """

    @swagger_auto_schema(
        operation_summary="Activar una cuenta de usuario",
        operation_description="Activa la cuenta del usuario mediante un token enviado por correo electrónico.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'token': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Token único generado para la activación de la cuenta",
                ),
            },
            required=['token'],
        ),
        responses={
            200: openapi.Response(
                description="Cuenta activada exitosamente.",
                examples={
                    "application/json": {"message": "Cuenta activada exitosamente. Ahora puedes iniciar sesión."}
                },
            ),
            400: openapi.Response(
                description="Error al activar la cuenta.",
                examples={
                    "application/json": {"error": "El enlace es inválido o ha expirado."}
                },
            ),
        },
    )
    def post(self, request):
        token = request.data.get('token')  # Token enviado en el cuerpo de la solicitud
        if not token:
            return Response({"error": "Token no proporcionado."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_id = signer.unsign(token, max_age=3600)
            user = get_object_or_404(CustomUser, pk=user_id)

            if user.is_active:
                return Response({"message": "Tu cuenta ya está activada. Por favor, inicia sesión."}, status=status.HTTP_200_OK)

            # Activar la cuenta
            user.is_active = True
            user.save()
            return Response({"message": "Cuenta activada exitosamente. Ahora puedes iniciar sesión."}, status=status.HTTP_200_OK)
        except SignatureExpired:
            return Response({"error": "El enlace ha expirado. Por favor, solicita un nuevo enlace."}, status=status.HTTP_400_BAD_REQUEST)
        except BadSignature:
            return Response({"error": "El enlace es inválido."}, status=status.HTTP_400_BAD_REQUEST)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import CustomUser, Carrera, Departamento, Instituto, Region


class ObtenerInformacionJerarquica(APIView):
    """
    Endpoint para obtener información jerárquica según el nivel del grupo del usuario.
    """
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_summary="Obtener información jerárquica",
        operation_description="""
            Este endpoint devuelve la información jerárquica relacionada al nivel del usuario autenticado.
            
            La jerarquía de niveles es la siguiente:
            - Nacional: Muestra todas las regiones, instituciones, departamentos, carreras y usuarios.
            - Regional: Muestra las instituciones, departamentos, carreras y usuarios de la región del usuario.
            - Institucional: Muestra los departamentos, carreras y usuarios del instituto del usuario.
            - Departamental: Muestra las carreras y usuarios del departamento del usuario.
            - Individual: Muestra la información de la carrera y del usuario.
        """,
        responses={
            200: openapi.Response(
                description="Respuesta exitosa con la información jerárquica del nivel del usuario.",
                examples={
                    "application/json": {
                        "nivel": "nacional",
                        "nacion": {
                            "nombre": "Nación"
                        },
                        "regiones": [
                            {
                                "id": 1,
                                "nombre": "Región Sur",
                                "instituciones": [
                                    {
                                        "id": 101,
                                        "nombre": "Instituto Tecnológico de Mérida",
                                        "departamentos": [
                                            {
                                                "id": 201,
                                                "nombre": "Departamento de Ciencias Básicas",
                                                "carreras": [
                                                    {
                                                        "id": 301,
                                                        "nombre": "Ingeniería en Sistemas Computacionales",
                                                        "usuarios": [
                                                            {
                                                                "id": 1,
                                                                "first_name": "Juan",
                                                                "last_name": "Pérez",
                                                                "email": "juan.perez@example.com"
                                                            }
                                                        ]
                                                    }
                                                ]
                                            }
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                }
            ),
            403: openapi.Response(
                description="El usuario no pertenece a ningún grupo o no tiene permisos para acceder a la información.",
                examples={
                    "application/json": {
                        "error": "El usuario no tiene permisos para acceder a esta información."
                    }
                }
            ),
            400: openapi.Response(
                description="Error relacionado con la asignación jerárquica del usuario.",
                examples={
                    "application/json": {
                        "error": "El usuario no tiene región asignada."
                    }
                }
            )
        }
    )
    def get(self, request):
        usuario = request.user
        grupo = usuario.groups.first()

        if not grupo:
            return Response({"error": "El usuario no pertenece a ningún grupo."}, status=403)

        # Niveles y lógica asociada
        niveles = {
            "Coordinador de Tutorias a Nivel Nacional": self.obtener_nacional,
            "Coordinador de Tutorias a Nivel Regional": self.obtener_regional,
            "Coordinador de Tutorias por Institucion": self.obtener_institucional,
            "Coordinador de Tutorias por Departamento": self.obtener_departamental,
            "Coordinador de Plan de Estudios": self.obtener_planestudios,
            "Tutores": self.obtener_individual,
        }

        # Determinar el nivel del usuario y ejecutar la lógica correspondiente
        nivel_funcion = niveles.get(grupo.name)
        if not nivel_funcion:
            return Response({"error": "El usuario no tiene permisos para acceder a esta información."}, status=403)

        # Ejecutar la función asociada al nivel
        return nivel_funcion(usuario)

    def obtener_nacional(self, usuario):
        """
        Devuelve todas las regiones, instituciones, departamentos, carreras y usuarios.
        """
        regiones = Region.objects.all()
        data = []
        for region in regiones:
            instituciones = Instituto.objects.filter(region=region)
            institucion_data = []
            print(region.nombre)
            for instituto in instituciones:
                print(instituto.nombre_completo)
                departamentos = Departamento.objects.filter(instituto=instituto)
                departamento_data = []
                for departamento in departamentos:
                    print(departamento.nombre)
                    carreras = Carrera.objects.filter(departamento=departamento)
                    carrera_data = []
                    for carrera in carreras:
                        # Filtrar usuarios que no son coordinadores
                        usuarios = CustomUser.objects.filter(
                            carrera=carrera
                        ).exclude(
                            groups__name__in=[
                                "Coordinador de Tutorias por Departamento",
                                "Coordinador de Tutorias por Institucion",
                                "Coordinador de Tutorias a Nivel Regional",
                                "Coordinador de Tutorias a Nivel Nacional",
                                "Coordinador de Plan de Estudios"
                            ]
                        ).values("id", "first_name", "last_name", "email")
                        carrera_data.append({
                            "id": carrera.cve_carrera,
                            "nombre": carrera.nombre,
                            "usuarios": list(usuarios)
                        })
                    departamento_data.append({
                        "id": departamento.cve_depto,
                        "nombre": departamento.nombre,
                        "carreras": carrera_data
                    })
                institucion_data.append({
                    "id": instituto.cve_inst,
                    "nombre": instituto.nombre_completo,
                    "departamentos": departamento_data
                })
            data.append({
                "id": region.cve_region,
                "nombre": region.nombre,
                "instituciones": institucion_data
            })

        return Response({
            "nivel": "nacional",
            "nacion": {"nombre": "Nación"},
            "regiones": data,
        })

    def obtener_regional(self, usuario):
        """
        Devuelve la región asociada al usuario, con sus instituciones, departamentos, carreras y usuarios.
        """
        region = usuario.Region
        if not region:
            return Response({"error": "El usuario no tiene región asignada."}, status=400)

        instituciones = Instituto.objects.filter(region=region)
        institucion_data = []
        for instituto in instituciones:
            departamentos = Departamento.objects.filter(instituto=instituto)
            departamento_data = []
            for departamento in departamentos:
                carreras = Carrera.objects.filter(departamento=departamento)
                carrera_data = []
                for carrera in carreras:
                    # Filtrar usuarios que no son coordinadores
                    usuarios = CustomUser.objects.filter(
                        carrera=carrera
                    ).exclude(
                        groups__name__in=[
                            "Coordinador de Plan de Estudios",
                            "Coordinador de Tutorias por Departamento",
                            "Coordinador de Tutorias por Institucion",
                            "Coordinador de Tutorias a Nivel Regional",
                            "Coordinador de Tutorias a Nivel Nacional"
                        ]
                    ).values("id", "first_name", "last_name", "email")
                    carrera_data.append({
                        "id": carrera.cve_carrera,
                        "nombre": carrera.nombre,
                        "usuarios": list(usuarios)
                    })
                departamento_data.append({
                    "id": departamento.cve_depto,
                    "nombre": departamento.nombre,
                    "carreras": carrera_data
                })
            institucion_data.append({
                "id": instituto.cve_inst,
                "nombre": instituto.nombre_completo,
                "departamentos": departamento_data
            })

        return Response({
            "nivel": "regional",
            "nacion": {"nombre": "Nación"},
            "region": {
                "id": region.cve_region,
                "nombre": region.nombre,
                "instituciones": institucion_data,
            }
        })

    def obtener_institucional(self, usuario):
        """
        Devuelve el instituto asociado al usuario, con sus departamentos, carreras y usuarios.
        """
        instituto = usuario.instituto
        if not instituto:
            return Response({"error": "El usuario no tiene instituto asignado."}, status=400)

        departamentos = Departamento.objects.filter(instituto=instituto)
        departamento_data = []
        for departamento in departamentos:
            carreras = Carrera.objects.filter(departamento=departamento)
            carrera_data = []
            for carrera in carreras:
                # Filtrar usuarios que no son coordinadores
                usuarios = CustomUser.objects.filter(
                    carrera=carrera
                ).exclude(
                    groups__name__in=[
                        "Coordinador de Plan de Estudios",
                        "Coordinador de Tutorias por Departamento",
                        "Coordinador de Tutorias por Institucion",
                        "Coordinador de Tutorias a Nivel Regional",
                        "Coordinador de Tutorias a Nivel Nacional"
                    ]
                ).values("id", "first_name", "last_name", "email")
                carrera_data.append({
                    "id": carrera.cve_carrera,
                    "nombre": carrera.nombre,
                    "usuarios": list(usuarios)
                })
            departamento_data.append({
                "id": departamento.cve_depto,
                "nombre": departamento.nombre,
                "carreras": carrera_data
            })

        return Response({
            "nivel": "institucional",
            "nacion": {"nombre": "Nación"},
            "region": {
                "id": instituto.region.cve_region,
                "nombre": instituto.region.nombre,
            },
            "instituto": {
                "id": instituto.cve_inst,
                "nombre": instituto.nombre_completo,
                "departamentos": departamento_data,
            }
        })

    def obtener_departamental(self, usuario):
        """
        Devuelve el departamento asociado al usuario, con sus carreras y usuarios.
        """
        departamento = usuario.departamento
        if not departamento:
            return Response({"error": "El usuario no tiene departamento asignado."}, status=400)

        carreras = Carrera.objects.filter(departamento=departamento)
        carrera_data = []
        for carrera in carreras:
            # Filtrar usuarios que no son coordinadores
            usuarios = CustomUser.objects.filter(
                carrera=carrera
            ).exclude(
                groups__name__in=[
                    "Coordinador de Plan de Estudios",
                    "Coordinador de Tutorias por Departamento",
                    "Coordinador de Tutorias por Institucion",
                    "Coordinador de Tutorias a Nivel Regional",
                    "Coordinador de Tutorias a Nivel Nacional"
                ]
            ).values("id", "first_name", "last_name", "email")
            carrera_data.append({
                "id": carrera.cve_carrera,
                "nombre": carrera.nombre,
                "usuarios": list(usuarios)
            })

        return Response({
            "nivel": "departamento",
            "nacion": {"nombre": "Nación"},
            "region": {
                "id": departamento.instituto.region.cve_region,
                "nombre": departamento.instituto.region.nombre,
            },
            "instituto": {
                "id": departamento.instituto.cve_inst,
                "nombre": departamento.instituto.nombre_completo,
            },
            "departamento": {
                "id": departamento.cve_depto,
                "nombre": departamento.nombre,
                "carreras": carrera_data,
            }
        })
    def obtener_planestudios(self, usuario):
        """
        Devuelve el departamento asociado al usuario, con sus carreras y usuarios.
        """
        plan_estudios = usuario.carrera
        if not plan_estudios:
            return Response({"error": "El usuario no tiene departamento asignado."}, status=400)

        #usuarios = Carrera.objects.filter(carrera=plan_estudios)
        usuarios_data = []
        #for usuario in usuarios:
            # Filtrar usuarios que no son coordinadores
        usuarios = CustomUser.objects.filter(
        carrera=plan_estudios
        ).exclude(
            groups__name__in=[
                "Coordinador de Plan de Estudios",
                "Coordinador de Tutorias por Departamento",
                "Coordinador de Tutorias por Institucion",
                "Coordinador de Tutorias a Nivel Regional",
                "Coordinador de Tutorias a Nivel Nacional"
            ]
        ).values("id", "first_name", "last_name", "email")
        """ usuarios_data.append({
            #"id": usuario.id,
            #"nombre": usuario.first_name,
            #"carrera":usuario.carrera.nombre,
            "":list(usuarios)
        }) """

        return Response({
            "nivel": "plan_estudios",
            "nacion": {"nombre": "Nación"},
            "region": {
                "id": plan_estudios.departamento.instituto.region.cve_region,
                "nombre": plan_estudios.departamento.instituto.region.nombre,
            },
            "instituto": {
                "id": plan_estudios.departamento.instituto.cve_inst,
                "nombre": plan_estudios.departamento.instituto.nombre_completo,
            },
            "departamento": {
                "id": plan_estudios.departamento.cve_depto,
                "nombre": plan_estudios.departamento.nombre,
            },
            "carrera": {
                "id": plan_estudios.cve_carrera,
                "nombre": plan_estudios.nombre,
                "usuarios": usuarios
                
            },
            
            
        })
    def obtener_individual(self, usuario):
        """
        Devuelve la información del tutor y la jerarquía a la que pertenece.
        """
        carrera = usuario.carrera
        if not carrera:
            return Response({"error": "El usuario no tiene carrera asignada."}, status=400)
        carrera = usuario
        return Response({ 
            "nivel": "individual",
            "nacion": {"nombre": "Nación"},
            "region": {
                "id": carrera.departamento.instituto.region.cve_region,
                "nombre": carrera.departamento.instituto.region.nombre,
            },
            "instituto": {
                "id": carrera.departamento.instituto.cve_inst,
                "nombre": carrera.departamento.instituto.nombre_completo,
            },
            "departamento": {
                "id": carrera.departamento.cve_depto,
                "nombre": carrera.departamento.nombre,
            },
            "carrera": {
                "id": carrera.cve_carrera,
                "nombre": carrera.nombre,
            },
            "usuario": {
                "id": usuario.id,
                "nombre": f"{usuario.first_name} {usuario.last_name}",
                "email": usuario.email,
            }
        })


from django.core.exceptions import PermissionDenied


class UserRelationUpdateAPIView(APIView):
    """
    API para actualizar las relaciones jerárquicas de un usuario.
    """
    def put(self, request, pk, *args, **kwargs):
        """
        Actualiza las relaciones de carrera, departamento, instituto y región para un usuario.
        """
        try:
            user = CustomUser.objects.get(pk=pk)  # Obtener el usuario por ID
        except CustomUser.DoesNotExist:
            return Response({"error": "El usuario no existe."}, status=status.HTTP_404_NOT_FOUND)

        serializer = UserRelationSerializer(user, data=request.data, partial=True)  # Validar los datos
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": "success",
                "message": "Relaciones actualizadas correctamente.",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        return Response({
            "status": "error",
            "message": "Datos inválidos.",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
        
#AQUI
class ReportePorAplicacionArgumento4View(APIView):
    """
    Endpoint para obtener reportes filtrados por aplicación y un único argumento adicional
    (Instituto, Departamento, Carrera, o Usuario).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, cve_aplic, tipo=None, valor=None):
        try:
            # Validar que la aplicación existe
            aplicacion = get_object_or_404(DatosAplicacion, pk=cve_aplic)

            if aplicacion.fecha_fin is None:
                return Response({"error": "La aplicación aún no ha finalizado."}, status=status.HTTP_400_BAD_REQUEST)

            # Obtener el grupo del usuario
            grupo_usuario = request.user.groups.first()
            usuario_token = CustomUser.objects.get(email=request.user)
            if not grupo_usuario:
                return Response({"error": "El usuario no pertenece a ningún grupo."}, status=status.HTTP_403_FORBIDDEN)

            # Mapear los niveles
            nivel_grupo = {
                "Coordinador de Tutorias a Nivel Nacional": "nacion",
                "Coordinador de Tutorias a Nivel Regional": "region",
                "Coordinador de Tutorias por Institucion": "instituto",
                "Coordinador de Tutorias por Departamento": "departamento",
                "Coordinador de Plan de Estudios": "planestudios",
                "Tutores": "tutor",
            }.get(grupo_usuario.name)

            if not nivel_grupo:
                return Response({"error": f"El grupo '{grupo_usuario.name}' no tiene un nivel asignado."},
                                status=status.HTTP_400_BAD_REQUEST)

            niveles = [
                "Coordinador de Tutorias a Nivel Nacional",
                "Coordinador de Tutorias a Nivel Regional",
                "Coordinador de Tutorias por Institucion",
                "Coordinador de Tutorias por Departamento",
                "Coordinador de Plan de Estudios",
                "Tutores",
            ]

            # Validar que no se consulte el mismo nivel del grupo del usuario
            if tipo and tipo.lower() == nivel_grupo:
                return Response(
                    {"error": "No puedes consultar reportes del mismo nivel al que perteneces."},
                    status=status.HTTP_403_FORBIDDEN
                )

            nivel_index_usuario = niveles.index(grupo_usuario.name)

            # Caso 1: Consulta sin tipo ni valor (reporte asociado al usuario actual)
            if not tipo and not valor:
                reportes = Reporte.objects.filter(referencia_id=cve_aplic, nivel=grupo_usuario.name)
                if not reportes.exists():
                    return Response({"error": "No se encontraron reportes para el grupo del usuario autenticado."},
                                    status=status.HTTP_404_NOT_FOUND)

                # Obtener el último reporte
                filtros = {
                "nacion": lambda: reportes.get(region=usuario_token.Region),
                "region": lambda: reportes.get( region=usuario_token.Region),
                "instituto": lambda: reportes.get( institucion=usuario_token.instituto),
                "departamento": lambda: reportes.get(departamento=usuario_token.departamento),
                "planestudios": lambda: reportes.get(carrera=usuario_token.carrera),
                "tutor": lambda: reportes.get(usuario_generador= usuario_token),
                }
                reporte = filtros[nivel_grupo]()
                #reporte=reporte_filtrado.last()
                #reporte = reportes.get()
                respuesta = {
                    "texto_fortalezas": reporte.texto_fortalezas ,
                    "texto_oportunidades": reporte.texto_oportunidades ,
                    "observaciones": reporte.observaciones,
                    "datos_promedios": reporte.datos_promedios ,
                    "nivel": reporte.nivel ,
                    #"usuario_generador": reporte.usuario_generador.email if reporte.usuario_generador else None,
                    # "institucion": reporte.institucion.nombre_completo if reporte.institucion else None,
                    # "departamento": reporte.departamento.nombre  if reporte.departamento else None,
                    # "carrera": reporte.carrera.nombre if reporte.carrera else None,
                }
                carrera = reporte.carrera.nombre if reporte and   reporte.carrera else None
                departamento = reporte.departamento.nombre  if reporte  and reporte.departamento else None
                instituto = reporte.institucion.nombre_completo if reporte and reporte.institucion else None
                region =  reporte.region.nombre if reporte and reporte.region else None
                datos_nivel ={
                    
                    "nombre": None,
                    "apellido": None,
                    "email":None,
                    "edad":None,
                    "carrera" : carrera,
                    "departamento": departamento,
                    "instituto": instituto,
                    "region": region
                    
                }
                return Response({"Datos":datos_nivel,"detalle": respuesta, "resultados": []}, status=status.HTTP_200_OK)

            nivel_consultado = {
                "region": "Coordinador de Tutorias a Nivel Regional",
                "instituto": "Coordinador de Tutorias por Institucion",
                "departamento": "Coordinador de Tutorias por Departamento",
                "planestudios": "Coordinador de Plan de Estudios",
                "tutor": "Tutores",
            }.get(tipo.lower())

            if not nivel_consultado:
                return Response(
                    {"error": f"El tipo '{tipo}' no es válido. Use 'region', 'instituto', 'departamento', 'planestudios' o 'tutor'."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validar jerarquía entre nivel del usuario y nivel consultado
            nivel_index_consultado = niveles.index(nivel_consultado)-1
            if nivel_index_consultado < nivel_index_usuario:
                return Response(
                    {"error": "No tienes permiso para consultar niveles superiores a tu jerarquía."},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Caso 2: Consulta con tipo y valor
            filtros = {
                "region": lambda: Reporte.objects.filter(referencia_id=cve_aplic, region=get_object_or_404(Region, pk=valor)),
                "instituto": lambda: Reporte.objects.filter(referencia_id=cve_aplic, institucion=get_object_or_404(Instituto, pk=valor)),
                "departamento": lambda: Reporte.objects.filter(referencia_id=cve_aplic, departamento=get_object_or_404(Departamento, pk=valor)),
                "planestudios": lambda: Reporte.objects.filter(referencia_id=cve_aplic, carrera=get_object_or_404(Carrera, pk=valor)),
                "tutor": lambda: Reporte.objects.filter(referencia_id=cve_aplic, usuario_generador=get_object_or_404(CustomUser, pk=valor)),
            }

            if tipo.lower() not in filtros:
                return Response({"error": f"El tipo '{tipo}' no es válido."}, status=status.HTTP_400_BAD_REQUEST)

            reportes_consultados = filtros[tipo.lower()]()
            if not reportes_consultados.exists():
                return Response({"error": "No se encontraron reportes para el filtro especificado."},
                                status=status.HTTP_404_NOT_FOUND)

            # Obtener reportes del grupo que hizo la consulta
            reportes_usuario = Reporte.objects.filter(referencia_id=cve_aplic, nivel=nivel_consultado)
            if not reportes_usuario.exists():
                return Response({"error": "No se encontraron reportes para el nivel consultado."},
                                status=status.HTTP_404_NOT_FOUND)

            # Procesar reportes entre niveles
            resultados = []
            for nivel in niveles[nivel_index_usuario:nivel_index_consultado +1]:
                reportes = Reporte.objects.filter(referencia_id=cve_aplic, nivel=nivel)
                if not reportes.exists():
                    continue

                # Calcular promedios de indicadores por nivel
                promedios_indicadores = defaultdict(list)
                for reporte in reportes:
                    if reporte.datos_promedios:
                        for indicador, data in reporte.datos_promedios.items():
                            promedios_indicadores[indicador].append(data["prom_score"])

                # Agregar los promedios agregados al resultado
                aggregated_scores = {
                    indicador: sum(scores) / len(scores) for indicador, scores in promedios_indicadores.items()
                }
                resultados.append({
                    "nivel": nivel,
                    "promedios_indicadores": aggregated_scores
                })

            # Obtener el último reporte del grupo del usuario
            reporte_usuario = reportes_consultados.get(nivel=nivel_consultado)
            
            respuesta_usuario = {
                "texto_fortalezas": reporte_usuario.texto_fortalezas ,
                "texto_oportunidades": reporte_usuario.texto_oportunidades ,
                "observaciones": reporte_usuario.observaciones ,
                "datos_promedios": reporte_usuario.datos_promedios ,
                "nivel": reporte_usuario.nivel ,
                #"usuario_generador": reporte_usuario.usuario_generador.email if reporte_usuario and reporte_usuario.usuario_generador else None,
                #"institucion": reporte_usuario.institucion.nombre_completo if reporte_usuario.institucion else None,
                #"departamento": reporte_usuario.departamento.nombre if reporte_usuario.departamento else None,
                #"carrera": reporte_usuario.carrera.nombre  if reporte_usuario.carrera else None,
            }
            edad = (
            date.today().year - reporte_usuario.usuario_generador.fecha_nacimiento.year
            - ((date.today().month, date.today().day) < 
            (reporte_usuario.usuario_generador.fecha_nacimiento.month, reporte_usuario.usuario_generador.fecha_nacimiento.day))
            if reporte_usuario and reporte_usuario.usuario_generador  and tipo == "tutor" and reporte_usuario.usuario_generador.fecha_nacimiento
            else None
            
            )
            carrera = reporte_usuario.carrera.nombre if reporte_usuario  and reporte_usuario.carrera else None
            departamento = reporte_usuario.departamento.nombre  if reporte_usuario  and reporte_usuario.departamento else None
            instituto = reporte_usuario.institucion.nombre_completo if reporte_usuario and reporte_usuario.institucion else None
            region =  reporte_usuario.region.nombre if reporte_usuario and reporte_usuario.region else None
            datos_usuario ={
                
                "nombre": reporte_usuario.usuario_generador.first_name if reporte_usuario and tipo.lower() =="tutor" and reporte_usuario.usuario_generador else None,
                "apellido":reporte_usuario.usuario_generador.last_name if reporte_usuario and tipo.lower() =="tutor" and reporte_usuario.usuario_generador else None,
                "email":reporte_usuario.usuario_generador.email if reporte_usuario and tipo.lower() == "tutor" and reporte_usuario.usuario_generador else None,
                "edad":edad,
                "carrera" : carrera,
                "departamento": departamento,
                "instituto": instituto,
                "region": region
                
            }
            return Response({
                "Datos": datos_usuario,
                "detalle": respuesta_usuario,
                "resultados": resultados
            }, status=status.HTTP_200_OK)

        except PermissionDenied as e:
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            return Response({"error": f"Error interno del servidor: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            

