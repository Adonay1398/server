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
    queryset = CustomUser.objects.all()
    serializer_class = TutorsRegistrationSerializer
    permission_classes = [AllowAny]
    
    
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

    def get(self, request, *args, **kwargs):
        user = request.user

        # Obtener las aplicaciones asignadas al usuario
        aplicaciones_asignadas = DatosAplicacion.objects.filter(asignaciones__usuario=user).distinct()
        print(f"Aplicaciones asignadas al usuario: {aplicaciones_asignadas}")

        if not aplicaciones_asignadas.exists():
            return Response({"on_hold": {"current": [], "past": []}, "submited": []}, status=200)

        on_hold_current = []
        submitted = []

        for aplicacion in aplicaciones_asignadas:
            for cuestionario in aplicacion.cuestionario.all():  # Relación ManyToMany
                preguntas_contestadas = Respuesta.objects.filter(
                    user=user, pregunta__cuestionario=cuestionario, cve_aplic=aplicacion
                ).count()
                total_preguntas = cuestionario.preguntas.count()
                asignacion = AsignacionCuestionario.objects.filter(
                    usuario=user, cuestionario=cuestionario, aplicacion=aplicacion
                ).first()
                cuestionario_data = {
                    "cve_cuestionario": cuestionario.cve_cuestionario,
                    "nombre_corto": cuestionario.nombre_corto,
                    "is_active": cuestionario.is_active,
                    "fecha_inicio": cuestionario.fecha_inicio,
                    "fecha_fin": cuestionario.fecha_fin,
                    "is_past": cuestionario.fecha_fin and cuestionario.fecha_fin < timezone.now(),
                    "fechas_constestado": asignacion.fecha_completado ,
                    "aplicaciones": [{"cve_aplic": aplicacion.cve_aplic}],
                    "total_preguntas": total_preguntas,
                    "preguntas_contestadas": preguntas_contestadas,
                }

                # Clasificar en "submitted" o "on_hold"
                if preguntas_contestadas == total_preguntas:
                    submitted.append(cuestionario_data)
                else:
                    on_hold_current.append(cuestionario_data)

        return Response({
            "on_hold": {"current": on_hold_current, "past": []},
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

    
    def get(self, request, Cuestionario_id,aplicacion_id ,*args, **kwargs):
        # Serializar datos del usuario con el contexto adicional
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
        cuestionario_id = request.data.get('cuestionario_id')
        print(cuestionario_id)  # Verifica los parámetros enviados en la solicitud

        if not cuestionario_id:
            return Response(
                {"error": "Debe proporcionar un ID de cuestionario válido."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Pasar el ID del cuestionario al serializador a través del contexto
        serializer = UserRelatedDataReporteSerializer(
            request.user,
            context={"request": request, "cuestionario_id": cuestionario_id}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


        


class ResponderPreguntaView(APIView):
    

    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "id_pregunta": openapi.Schema(type=openapi.TYPE_STRING, description="ID de la pregunta."),
                "respuesta": openapi.Schema(type=openapi.TYPE_STRING, description="Valor de la respuesta."),
                "cve_aplic": openapi.Schema(type=openapi.TYPE_STRING, description="Clave de la aplicación.")
            },
            required=["id_pregunta", "respuesta", "cve_aplic"]
        ),
        responses={
            201: "Respuesta registrada.",
            200: "Respuesta actualizada.",
            400: "Error: Datos incompletos.",
            404: "Error: Aplicación o pregunta no encontrada.",
            500: "Error interno del servidor."
        }
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
                asignacion.fecha_completado = now()  # Guardar la fecha actual
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




""" 
class JerarquiaView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        
        user = request.user
        group = user.groups.first()
        nivel = request.query_params.get('nivel', None)
        identificador = request.query_params.get('identificador', None)

        if not group:
            return Response({'error': 'El usuario no pertenece a ningún grupo'}, status=403)

        # Verificar el grupo y aplicar las restricciones correspondientes
        if group.name == 'Coordinador de Tutorias a Nivel Nacional':
            # Puede ver regiones
            if nivel == 'region':
                regiones = Region.objects.all()
                if identificador:
                    regiones = regiones.filter(nacion_id=identificador)
                serializer = RegionSerializer(regiones, many=True)
                return Response(serializer.data)

        elif group.name == 'Coordinador de Tutorias a Nivel Region':
            # Puede ver institutos
            if nivel == 'instituto':
                institutos = Instituto.objects.filter(region__coordinador=user)
                if identificador:
                    institutos = institutos.filter(region_id=identificador)
                serializer = InstitutoSerializer(institutos, many=True)
                return Response(serializer.data)

        elif group.name == 'Coordinador de Tutorias a Nivel Instituto':
            # Puede ver departamentos
            if nivel == 'departamento':
                departamentos = Departamento.objects.filter(instituto__coordinador=user)
                if identificador:
                    departamentos = departamentos.filter(instituto_id=identificador)
                serializer = DepartamentoSerializer(departamentos, many=True)
                return Response(serializer.data)
        elif group.name == 'Coordinador de Tutorias a Nivel Departamento':
            if nivel == 'departamento': 
                carrera =  Carrera.objects.filter(departamento__coordinador=user)
                if identificador:
                    carrera = carrera.filter(departamento_id=identificador)
                serializer = CarreraSerializer(carrera, many=True)
                return Response(serializer.data)
        elif group.name == 'Coordinador de Plan de Estudios':
            if nivel == 'plan_estudios':
                plan_estudios = CustomUser.objects.all()
                serializer = UserRelatedDataSerializer(plan_estudios, many=True)
                return Response(serializer.data)
        
        return Response({'error': 'No autorizado'}, status=403)

 """
class PreguntaView(APIView):
    """
    Vista para manejar solicitudes relacionadas con las preguntas de un cuestionario.
    """
    permission_classes = [IsAuthenticated]

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
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "cuestionario": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID del cuestionario."),
                "grupo": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID del grupo."),
                "aplicacion": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID de la aplicación."),
            },
            required=["cuestionario", "grupo", "aplicacion"]
        ),
        responses={
            200: "Cuestionario asignado exitosamente al grupo.",
            400: "Error en los parámetros proporcionados.",
            404: "Cuestionario, grupo o aplicación no encontrados.",
            500: "Error interno del servidor.",
        }
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
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "cuestionario": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID del cuestionario."),
                "usuario": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID del usuario."),
                "cve_aplic": openapi.Schema(type=openapi.TYPE_STRING, description="Clave de la aplicación."),
            },
            required=["cuestionario", "usuario", "cve_aplic"]
        ),
        responses={
            200: "Cuestionario asignado exitosamente al usuario.",
            400: "Error en los parámetros proporcionados.",
            404: "Cuestionario, usuario o aplicación no encontrados.",
            500: "Error interno del servidor.",
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
        
class GenerateScoresView(APIView):
        
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
            request_body=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "cuestionario": openapi.Schema(
                        type=openapi.TYPE_INTEGER,
                        description="ID del cuestionario para el cual se generarán los scores."
                    )
                },
                required=["cuestionario"]
            ),
            responses={
                200: openapi.Response(
                    description="Scores generados exitosamente.",
                    examples={
                        "application/json": {
                            "message": "Análisis completo realizado exitosamente."
                        }
                    }
                ),
                400: openapi.Response(
                    description="Error en los parámetros proporcionados.",
                    examples={
                        "application/json": {
                            "error": "Debe proporcionar el ID del cuestionario."
                        }
                    }
                ),
                403: openapi.Response(
                    description="Usuario no autorizado para realizar esta acción.",
                    examples={
                        "application/json": {
                            "error": "El usuario no pertenece a ningún grupo asignado."
                        }
                    }
                ),
                404: openapi.Response(
                    description="Cuestionario no encontrado.",
                    examples={
                        "application/json": {
                            "error": "El cuestionario proporcionado no existe."
                        }
                    }
                ),
                500: openapi.Response(
                    description="Error interno al calcular los scores.",
                    examples={
                        "application/json": {
                            "error": "Error al calcular scores: detalle del error."
                        }
                    }
                )
            }
        )
    def post(self, request, *args, **kwargs):
        usuario = request.user  # Usuario autenticado
        cuestionario_id = request.data.get('cuestionario')
        

        try:
            # 1. Validar si el usuario tiene un grupo asignado
            grupo = usuario.groups.first()  # Obtener el primer grupo del usuario
            if not grupo:
                return Response(
                    {"error": "El usuario no pertenece a ningún grupo asignado."},
                    status=status.HTTP_403_FORBIDDEN
                )
            cuestionario = Cuestionario.objects.get(pk=cuestionario_id)

            aplicacion = DatosAplicacion.objects.filter(cuestionario=cuestionario).last()
            # 2. Si el grupo NO es "Tutores", redirigir a otra lógica
            if grupo.name != "Tutores":
                # Función o lógica alternativa para otros grupos
                reporte= generar_reporte_por_grupo(usuario,aplicacion,cuestionario_id)
                return Response(reporte, status=status.HTTP_200_OK)

            # 3. Si el grupo ES "Tutores", continuar con el flujo existente
            if not cuestionario_id:
                return Response(
                    {"error": "Debe proporcionar el ID del cuestionario."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Obtener el cuestionario
            try:
                cuestionario = Cuestionario.objects.get(pk=cuestionario_id)
            except Cuestionario.DoesNotExist:
                return Response(
                    {"error": "El cuestionario proporcionado no existe."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Validar si existe una asignación para el usuario y cuestionario
            asignacion = AsignacionCuestionario.objects.filter(usuario=usuario, cuestionario=cuestionario).last()
            if not asignacion:
                return Response(
                    {"error": "No se encontró una asignación para este usuario y cuestionario."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validar si existe una aplicación asociada a la asignación
            aplicacion = asignacion.aplicacion
            if not aplicacion:
                return Response(
                    {"error": "No se encontró una aplicación asociada a la asignación."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Calcular los scores
            try:
                scores_constructos, scores_indicadores, reporte = calcular_scores(usuario, aplicacion)
            except Exception as e:
                return Response(
                    {"error": f"Error al calcular scores: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # Guardar los scores en la base de datos
            for constructo_obj, score in scores_constructos.items():
                if not isinstance(constructo_obj, Constructo):
                    constructo_obj = Constructo.objects.get(pk=constructo_obj.pk)

                ScoreConstructo.objects.update_or_create(
                    aplicacion=aplicacion,
                    usuario=usuario,
                    constructo=constructo_obj,
                    defaults={"score": score}
                )

            # Respuesta final
            return Response(
                {"message": "Análisis completo realizado exitosamente."},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"error": f"Error inesperado: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ListarReportesAPIView(APIView):
    """
    Endpoint para listar los reportes de un usuario.
    """

    def get(self, request):
        usuario = request.user
        reportes = RetroChatGPT.objects.filter(usuario=usuario).order_by('-creado_en')
        serializer = RetroChatGPTSerializer(reportes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    


class GenerarVerReporteView(APIView):
    """
    Vista para generar o recuperar el reporte y los promedios según el usuario y el cuestionario.
    """
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
            request_body=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    # No se especifica body, ya que usa datos del usuario autenticado
                }
            ),
            responses={
                200: openapi.Response(
                    description="Reporte y promedios generados exitosamente.",
                    examples={
                        "application/json": {
                            "reporte": {
                                "id": 1,
                                "texto_fortalezas": "Fortalezas del grupo",
                                "texto_oportunidades": "Oportunidades del grupo",
                                "perfil": "Observaciones específicas"
                            },
                            "promedios_indicadores": [
                                {"indicador": "Indicador 1", "promedio": 4.5},
                                {"indicador": "Indicador 2", "promedio": 3.8}
                            ],
                            "promedios_constructos": [
                                {"constructo": "Constructo 1", "promedio": 4.2},
                                {"constructo": "Constructo 2", "promedio": 3.9}
                            ]
                        }
                    }
                ),
                403: openapi.Response(
                    description="El usuario no pertenece a un grupo válido.",
                    examples={
                        "application/json": {
                            "error": "El usuario no pertenece a ningún grupo."
                        }
                    }
                ),
                404: openapi.Response(
                    description="No se encontró un reporte válido.",
                    examples={
                        "application/json": {
                            "error": "No se encontró un reporte válido para el nivel especificado."
                        }
                    }
                ),
                500: openapi.Response(
                    description="Error interno del servidor.",
                    examples={
                        "application/json": {
                            "error": "Error inesperado: detalle del error."
                        }
                    }
                )
            }
        )
    def post(self, request, *args, **kwargs):
        usuario = request.user
        grupo = usuario.groups.first()

        if not grupo:
            return Response({"error": "El usuario no pertenece a ningún grupo."}, status=403)

        grupo_valido = {
            "Coordinador de Plan de Estudios": "plan_estudios",
            "Coordinador de Tutorias por Departamento": "departamento",
            "Coordinador de Tutorias por Institucion": "instituto",
            "Coordinador de Tutorias a Nivel Regional": "region",
            "Coordinador de Tutorias a Nivel Nacional": "nacion",
        }

        grupo_nombre = grupo.name if grupo else None

        if grupo_nombre not in grupo_valido:
            return Response({"error": "El grupo del usuario no es válido."}, status=403)

        nivel = grupo.name

        try:
            reporte = Reporte.objects.filter(
                nivel=nivel,
                referencia_id=usuario.id,
                usuario_generador=usuario
            ).order_by('-fecha_generacion').first()

            if not reporte:
                return Response({"error": "No se encontró un reporte válido para el nivel especificado y la referencia proporcionada."}, status=404)

            promedios_indicadores = IndicadorPromedio.objects.filter(
                nivel=nivel,
                grupo=grupo
            ).values('indicador__nombre', 'promedio')

            promedios_constructos = ScoreConstructo.objects.filter(
                usuario__groups=grupo
            ).values('constructo__descripcion').annotate(promedio=Avg('score'))

            response_data = {
                "reporte": {
                    "id": reporte.id,
                    "texto_fortalezas": reporte.texto_fortalezas,
                    "texto_oportunidades": reporte.texto_oportunidades,
                    
                    "perfil": reporte.observaciones,
                },
                "promedios_indicadores": [
                    {"indicador": prom["indicador__nombre"], "promedio": prom["promedio"]}
                    for prom in promedios_indicadores
                ],
                "promedios_constructos": [
                    {"constructo": prom["constructo__descripcion"], "promedio": prom["promedio"]}
                    for prom in promedios_constructos
                ]
            }

            return Response(response_data, status=200)

        except Exception as e:
            return Response({"error": f"Error inesperado: {str(e)}"}, status=500)

class GenerarRetroalimentacionView(APIView):
    """
    Vista para generar la retroalimentación basada en RetroChatGPT,
    promedios de constructos e indicadores.
    """
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
    manual_parameters=[],
    responses={
        200: openapi.Response(
            description="Reporte y promedios generados exitosamente.",
            examples={
                "application/json": {
                    "reporte": {
                        "id": 1,
                        "texto_fortalezas": "Fortalezas del grupo",
                        "texto_oportunidades": "Oportunidades del grupo",
                        "perfil": "Observaciones específicas"
                    },
                    "promedios_indicadores": [
                        {"indicador": "Indicador 1", "promedio": 4.5},
                        {"indicador": "Indicador 2", "promedio": 3.8}
                    ],
                    "promedios_constructos": [
                        {"constructo": "Constructo 1", "promedio": 4.2},
                        {"constructo": "Constructo 2", "promedio": 3.9}
                    ]
                }
            }
        ),
        403: openapi.Response(
            description="El usuario no pertenece a un grupo válido.",
            examples={
                "application/json": {
                    "error": "El usuario no pertenece a ningún grupo."
                }
            }
        ),
        404: openapi.Response(
            description="No se encontró un reporte válido.",
            examples={
                "application/json": {
                    "error": "No se encontró un reporte válido para el nivel especificado."
                }
            }
        ),
        500: openapi.Response(
            description="Error interno del servidor.",
            examples={
                "application/json": {
                    "error": "Error inesperado: detalle del error."
                }
            }
        )
    }
)
    def get(self, request, *args, **kwargs):
        usuario = request.user
        grupo = usuario.groups.first()

        if not grupo:
            return Response({"error": "El usuario no pertenece a ningún grupo."}, status=403)

        try:
            # Obtener la retroalimentación más reciente para el usuario autenticado
            
            retro = RetroChatGPT.objects.filter(
                usuario=usuario
            ).order_by('-cve_retro').first()

            if not retro:
                return Response({"error": "No se encontró retroalimentación para el usuario."}, status=404)

            # Obtener los promedios de indicadores
            promedios_indicadores = ScoreIndicador.objects.filter(
                usuario=usuario
            ).values('indicador__nombre').annotate(promedio=Avg('score')).distinct()

            # Obtener los promedios de constructos
            promedios_constructos = ScoreConstructo.objects.filter(
                usuario=usuario
            ).values('constructo__descripcion').annotate(promedio=Avg('score')).distinct()

            # Construir la respuesta
            response_data = {
                "retroalimentacion": {
                    "fortalezas": retro.texto1,
                    "oportunidades": retro.texto2,
                    #"observaciones": retro.texto3,
                    #"archivo_pdf": request.build_absolute_uri(retro.pdf_file.url) if retro.pdf_file else None,
                },
                "promedios_indicadores": [
                    {"indicador": prom["indicador__nombre"], "promedio": prom["promedio"]}
                    for prom in promedios_indicadores
                ],
                    "promedios_constructos": [
                        {"constructo": prom["constructo__descripcion"], "promedio": prom["promedio"]}
                        for prom in promedios_constructos
                    ]
            }
            return Response(response_data, status=200)

        except Exception as e:
            return Response({"error": f"Error inesperado: {str(e)}"}, status=500)
        
        
class NavegarNivelesAPIView(APIView):
    """
    Endpoint para navegar entre niveles jerárquicos.
    """
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'nivel', openapi.IN_QUERY, 
                description="Nivel actual desde el cual se navega. Valores posibles: 'region', 'instituto', 'departamento', 'carrera'.",
                type=openapi.TYPE_STRING,
                required=True
            ),
            openapi.Parameter(
                'id', openapi.IN_QUERY, 
                description="ID del elemento actual para consultar sus elementos inferiores.",
                type=openapi.TYPE_STRING,
                required=False
            )
        ],
        responses={
            200: openapi.Response(
                description="Lista de elementos del nivel inferior.",
                examples={
                    "application/json": {
                        "nivel": "instituto",
                        "datos": [
                            {"id": "123", "nombre": "Instituto ABC"},
                            {"id": "124", "nombre": "Instituto XYZ"}
                        ]
                    }
                }
            ),
            400: openapi.Response(
                description="Error en los parámetros proporcionados.",
                examples={
                    "application/json": {
                        "error": "El parámetro 'nivel' es obligatorio."
                    }
                }
            )
        }
    )
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


class InstitutoCarrerasView(APIView):
    """
    Endpoint para devolver la lista de institutos con solo el nombre y sus carreras.
    """
    permission_classes = [AllowAny]  # Opcional, si necesitas autenticación

    def get(self, request, *args, **kwargs):
        institutos = Instituto.objects.all()
        serializer = InstitutoSerializer(institutos, many=True)
        return Response(serializer.data, status=200)