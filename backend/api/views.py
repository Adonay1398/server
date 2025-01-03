from datetime import datetime, time
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from marshmallow import ValidationError
from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated, DjangoModelPermissions
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication   
from rest_framework_simplejwt.views import TokenObtainPairView
from .modul.GenerateAnalysGroups import generar_reporte_por_grupo
from .modul.analysis import calcular_scores
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import threading
from django.utils.timezone import now
from django.utils.timezone import make_aware

from .models import *
from .serializers import *
#from .utils import calcular_scores_jerarquicos, calcular_scores_tutor
#from api.modul.retro_chatgpt_service import generar_retro_jerarquica, procesar_cuestionarios,calcular_scores_jerarquicos
#from api.utils import calcular_scores_jerarquicos #verificar_autenticacion_y_jerarquia
from .permissions import IsAuthorizedUser

# ==========================
# USUARIOS
# ==========================

class UserRegistrationView(APIView):
    """
    Vista para el registro de nuevos usuarios.

    Esta clase maneja las solicitudes HTTP POST para registrar nuevos usuarios en el sistema.
    
    Atributos:
        queryset (QuerySet): Conjunto de consultas para todos los usuarios personalizados.
        serializer_class (Serializer): Clase de serializador para validar y guardar los datos del usuario.
    """
    queryset = CustomUser.objects.all()
    serializer_class = UserRegistrationSerializer
    def post(self, request, *args, **kwargs):
        """
            Maneja las solicitudes POST para registrar un nuevo usuario.

            Este método recibe los datos del usuario desde la solicitud, los valida utilizando
            el serializador correspondiente y, si son válidos, crea un nuevo registro de usuario.

            Args:
                request (Request): Objeto de solicitud que contiene los datos del usuario a registrar.
                *args: Argumentos adicionales.
                **kwargs: Argumentos de palabra clave adicionales.

            Returns:
                Response: Respuesta HTTP con los datos del usuario registrado y un código de estado 201 si la
                        creación es exitosa, o con los errores de validación y un código de estado 400 si
                        la validación falla.
        """
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
        aplicaciones_asignadas = DatosAplicacion.objects.filter(asignaciones__usuario=user).distinct()
        print(f"Aplicaciones asignadas al usuario: {aplicaciones_asignadas}")

        if not aplicaciones_asignadas.exists():
            return Response({"on_hold": {"current": [], "past": []}, "submited": []}, status=200)

        on_hold_current = []
        on_hold_past = []  # Inicializar la lista
        submitted = []

        for aplicacion in aplicaciones_asignadas:
            for cuestionario in aplicacion.cuestionario.all():  # Relación ManyToMany
                preguntas_contestadas = Respuesta.objects.filter(
                    user=user, pregunta__cuestionario=cuestionario, cve_aplic=aplicacion
                ).count()


                total_preguntas = cuestionario.preguntas.count()
                asignacion = AsignacionCuestionario.objects.filter(
                    usuario=user, aplicacion=aplicacion
                ).first()
                
                is_past = aplicacion.fecha_fin and make_aware(datetime.combine(aplicacion.fecha_fin, time.min)) < timezone.now()

                cuestionario_data = {
                    "cve_cuestionario": cuestionario.cve_cuestionario,
                    "nombre_corto": cuestionario.nombre_corto,
                    "is_active": cuestionario.is_active,
                    "fecha_inicio": aplicacion.fecha_inicion,
                    "fecha_fin": aplicacion.fecha_fin.strftime("%Y-%m-%d") if aplicacion.fecha_fin else None,
                    "fecha_limite": aplicacion.fecha_limite,
                    "is_past": is_past,
                    "fecha_completado": asignacion.fecha_completado if asignacion else None,
                    "aplicaciones": [{"cve_aplic": aplicacion.cve_aplic}],
                    "total_preguntas": total_preguntas,
                    "preguntas_contestadas": preguntas_contestadas,
                }

                # Clasificar en "submitted", "on_hold_current" o "on_hold_past"
                if preguntas_contestadas == total_preguntas:
                    submitted.append(cuestionario_data)
                elif is_past:
                    on_hold_past.append(cuestionario_data)
                else:
                    on_hold_current.append(cuestionario_data)

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
    
    def get(self, request, Cuestionario_id,aplicacion_id ,*args, **kwargs):
        """
        Maneja solicitudes GET para obtener datos relacionados con el usuario y un cuestionario específico.

        Parámetros:
        - `Cuestionario_id` (int): ID del cuestionario relacionado.
        - `aplicacion_id` (int): ID de la aplicación relacionada.

        Respuesta:
        - 200: Datos obtenidos exitosamente.
        - 401: No autorizado.
        """        
        serializer = UserRelatedDataSerializer(
        instance=request.user,
        context={
            "request": request,
            "Cuestionario_id": Cuestionario_id,
            "aplicacion": aplicacion_id
            }
        )

        return Response(serializer.data, status=status.HTTP_200_OK)
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
        operation_summary="Asignar cuestionario a un grupo",
        operation_description=(
            "Este endpoint asigna un cuestionario específico a todos los usuarios de un grupo. "
            "Requiere proporcionar el ID del cuestionario, el ID del grupo, y el ID de la aplicación."
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["cuestionario", "grupo", "aplicacion"],
            properties={
                "cuestionario": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="ID del cuestionario que se desea asignar."
                ),
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
                description="Cuestionario asignado exitosamente.",
                examples={
                    "application/json": {
                        "message": "Cuestionario asignado exitosamente al grupo"
                    }
                }
            ),
            400: openapi.Response(
                description="Solicitud inválida.",
                examples={
                    "application/json": {
                        "error": "Debe proporcionar cuestionario, grupo y aplicación"
                    }
                }
            ),
            404: openapi.Response(
                description="No se encontró el cuestionario, grupo o aplicación.",
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
        cuestionario_id = request.data.get('cuestionario', None)
        grupo_id = request.data.get('grupo', None)
        aplicacion_id = request.data.get('aplicacion', None)

        if not cuestionario_id or not grupo_id or not aplicacion_id:
            return Response({"error": "Debe proporcionar cuestionario, grupo y aplicación"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Obtener cuestionario, grupo y aplicación
            cuestionario = Cuestionario.objects.get(pk=cuestionario_id)
            grupo = Group.objects.get(pk=grupo_id)
            aplicacion = DatosAplicacion.objects.get(pk=aplicacion_id)
            usuarios = CustomUser.objects.filter(groups=grupo)

            for usuario in usuarios:
                AsignacionCuestionario.objects.get_or_create(
                    usuario=usuario,
                    cuestionario=cuestionario,
                    aplicacion=aplicacion
                )

            return Response({"message": "Cuestionario asignado exitosamente al grupo"}, status=status.HTTP_200_OK)

        except Cuestionario.DoesNotExist:
            return Response({"error": "Cuestionario no encontrado"}, status=status.HTTP_404_NOT_FOUND)
        except Group.DoesNotExist:
            return Response({"error": "Grupo no encontrado"}, status=status.HTTP_404_NOT_FOUND)
        except DatosAplicacion.DoesNotExist:
            return Response({"error": "Aplicación no encontrada"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AsignarCuestionarioUsuarioView(APIView):
    
    permission_classes = [AllowAny]
    @swagger_auto_schema(
        operation_summary="Asignar cuestionario a usuario",
        operation_description=(
            "Este endpoint asigna un cuestionario específico a un usuario dentro de una aplicación específica. "
            "Se debe proporcionar el ID del cuestionario, el ID del usuario y la clave de la aplicación (`cve_aplic`)."
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["cuestionario", "usuario", "cve_aplic"],
            properties={
                "cuestionario": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="ID del cuestionario a asignar."
                ),
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
                description="Cuestionario asignado exitosamente al usuario.",
                examples={
                    "application/json": {
                        "message": "Cuestionario asignado exitosamente al usuario"
                    }
                }
            ),
            400: openapi.Response(
                description="Faltan parámetros obligatorios o son inválidos.",
                examples={
                    "application/json": {
                        "error": "Debe proporcionar cuestionario, usuario y aplicación"
                    }
                }
            ),
            404: openapi.Response(
                description="No se encontró uno de los recursos especificados.",
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
                        "error": "Descripción del error interno."
                    }
                }
            )
        }
    )
    def post(self, request, *args, **kwargs):
        cuestionario_id = request.data.get('cuestionario', None)
        usuario_id = request.data.get('usuario', None)
        aplicacion_id = request.data.get('cve_aplic', None)
        
        print(cuestionario_id, usuario_id, aplicacion_id)
        if not cuestionario_id or not usuario_id or not aplicacion_id:
            return Response({"error": "Debe proporcionar cuestionario, usuario y aplicación"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Obtener cuestionario, usuario y aplicación
            cuestionario = Cuestionario.objects.get(pk=cuestionario_id)
            usuario = CustomUser.objects.get(pk=usuario_id)
            aplicacion = DatosAplicacion.objects.get(pk=aplicacion_id)

            # Crear la relación en AsignacionCuestionario
            AsignacionCuestionario.objects.get_or_create(
                usuario=usuario,
                cuestionario=cuestionario,
                aplicacion=aplicacion
            )

            return Response({"message": "Cuestionario asignado exitosamente al usuario"}, status=status.HTTP_200_OK)

        except Cuestionario.DoesNotExist:
            return Response({"error": "Cuestionario no encontrado"}, status=status.HTTP_404_NOT_FOUND)
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
        Cuestionario_id = request.data.get('Cuestionario_id')
        if not cve_aplic:
            return Response({"error": "El campo 'cve_aplic' es obligatorio."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Buscar la aplicación
            aplicacion = DatosAplicacion.objects.get(cve_aplic=cve_aplic)
            # Asumiendo que la relación es ForeignKey
            # Verificar si la aplicación ya está cerrada
            if aplicacion.fecha_fin and aplicacion.fecha_fin < now().date():
                return Response({"error": "La aplicación ya está cerrada."}, status=status.HTTP_400_BAD_REQUEST)

            # Marcar la aplicación como cerrada
            aplicacion.fecha_fin = now().date()
            aplicacion.save()
            theread = threading.Thread(target=generar_reporte_por_grupo, args=(request.user, aplicacion, Cuestionario_id))
            theread.start()
            
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

class ReportePorAplicacionView(APIView):
    """
    Endpoint para obtener los campos específicos de la tabla Reporte basado en la clave de aplicación.
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Obtener reporte por aplicación",
        operation_description="Este endpoint devuelve los campos específicos del reporte basado en la clave de la aplicación proporcionada.",
        manual_parameters=[
            openapi.Parameter(
                'cve_aplic',
                openapi.IN_PATH,
                description="Clave única de la aplicación.",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Reporte encontrado.",
                examples={
                    "application/json": {
                        "texto_fortalezas": "Texto de fortalezas del reporte.",
                        "texto_oportunidades": "Texto de oportunidades del reporte.",
                        "observaciones": "Observaciones adicionales del reporte.",
                        "datos_promedios": {
                            "Inteligencias múltiples": {
                                "prom_score": 60,
                                "constructos": [
                                    {"nombre": "Musical", "prom_score": 43},
                                    {"nombre": "Lógico-matemático", "prom_score": 70}
                                ]
                            },
                            "Personalidad": {
                                "prom_score": 75,
                                "constructos": [
                                    {"nombre": "Imaginación", "prom_score": 62},
                                    {"nombre": "Intelecto", "prom_score": 62}
                                ]
                            }
                        }
                    }
                }
            ),
            404: "Reporte no encontrado.",
            500: "Error interno del servidor."
        }
    )
    def get(self, request, *args, **kwargs):
        # Obtener la clave de la aplicación desde los parámetros de la URL
        cve_aplic = kwargs.get('cve_aplic')
        try:
            # Verificar si la aplicación existe
            aplicacion = DatosAplicacion.objects.get(pk=cve_aplic)

            # Buscar el reporte asociado a la aplicación
            reporte = Reporte.objects.filter(referencia_id=aplicacion.cve_aplic).first()

            if not reporte:
                return Response({"error": "Reporte no encontrado para esta aplicación."}, status=status.HTTP_404_NOT_FOUND)


            # Devolver los campos solicitados
            return Response({
                "texto_fortalezas": reporte.texto_fortalezas,
                "texto_oportunidades": reporte.texto_oportunidades,
                "observaciones": reporte.observaciones,
                "datos_promedios": reporte.datos_promedios,
            }, status=status.HTTP_200_OK)

        except DatosAplicacion.DoesNotExist:
            return Response({"error": "Aplicación no encontrada."}, status=status.HTTP_404_NOT_FOUND)
