from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated, DjangoModelPermissions
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import *
from .serializers import *
from .utils import calcular_scores_jerarquicos, calcular_scores_tutor
from api.modul.retro_chatgpt_service import procesar_cuestionarios
# ==========================
# USUARIOS
# ==========================
class CustomUserListView(generics.ListCreateAPIView):
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

class CuestionarioStatusView(generics.RetrieveAPIView):
    """
    Obtener el estado de los cuestionarios para el usuario autenticado.
    """
    serializer_class = CuestionarioStatusSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        serializer = CuestionarioStatusSerializer(
            data={}, 
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)

# ==========================
# RESPUESTAS
# ==========================
class StoreResponsesView(APIView):
    """
    Guardar respuestas y calcular scores para constructos e indicadores.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
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

class GenerateAggregateScoreView(APIView):
    """
    Calcular y guardar el promedio general de indicadores para un nivel y referencia específicos.
    """
    def post(self, request, *args, **kwargs):
        nivel = request.data.get('nivel')
        referencia_id = request.data.get('referencia_id')
        cuestionario_id = request.data.get('cuestionario_id')
        campo = request.data.get('campo')  # Campo según el nivel (por ejemplo: 'carrera', 'departamento')

        if not nivel or not referencia_id or not cuestionario_id or not campo:
            return Response({"error": "Faltan datos obligatorios."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Obtener el cuestionario
            cuestionario = Cuestionario.objects.get(pk=cuestionario_id)
            filtros = {"indicador__constructos__preguntas_const1__cuestionario": cuestionario}

            # Filtrar por el nivel y la referencia_id
            if nivel == "carrera":
                filtros["usuario__carrera_id"] = referencia_id
            elif nivel == "departamento":
                filtros["usuario__carrera__departamento_id"] = referencia_id
            elif nivel == "instituto":
                filtros["usuario__carrera__departamento__instituto_id"] = referencia_id
            else:
                return Response({"error": "Nivel no válido."}, status=status.HTTP_400_BAD_REQUEST)

            # Obtener los indicadores y calcular el promedio
            scores_indicadores = ScoreIndicador.objects.filter(**filtros).distinct()
            total_score = sum(score.score for score in scores_indicadores)
            count = scores_indicadores.count()
            average_score = total_score / count if count > 0 else 0

            # Actualizar o crear el AggregateIndicatorScore
            AggregateIndicatorScore.objects.update_or_create(
                nivel=nivel,
                referencia_id=referencia_id,
                cuestionario=cuestionario,
                defaults={"average_score": average_score}
            )

            # Obtener el usuario que está generando el reporte (generalmente request.user)
            usuario = request.user

            # Llamar a generar_reporte con los 4 parámetros
            reporte = ReporteService.generar_reporte(nivel, referencia_id, usuario, campo)

            return Response({
                "message": "Promedio calculado, guardado y reporte generado.",
                "reporte_id": reporte.id,
                "fortalezas": reporte.texto_fortalezas,
                "oportunidades": reporte.texto_oportunidades
            }, status=status.HTTP_201_CREATED)

        except Cuestionario.DoesNotExist:
            return Response({"error": "Cuestionario no encontrado."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserRelatedDataView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        serializer = UserRelatedDataSerializer(
            instance=request.user,  # Pasar el usuario autenticado como instancia
            context={'request': request}  # Contexto necesario para el serializador
        )
        return Response(serializer.data)
    
CAMPO_NIVEL = {
    'carrera': 'carrera_id',
    'departamento': 'departamento_id',
    'instituto': 'instituto_id'
}
class GenerarReporteAPIView(APIView):
    def post(self, request, *args, **kwargs):
        # Obtener los datos del cuerpo de la solicitud
        nivel = request.data.get('nivel')
        referencia_ids = request.data.get('referencia_ids')  # Ahora esperamos una lista de IDs
        usuario = request.user  # Asumimos que tienes un sistema de autenticación

        # Validar que los parámetros estén presentes
        if not nivel or not referencia_ids:
            return Response({"detail": "Nivel y referencia_ids son requeridos."}, status=status.HTTP_400_BAD_REQUEST)

        # Verificar que el nivel esté en el diccionario
        if nivel not in ['carrera', 'departamento', 'instituto']:
            return Response({"detail": "Nivel no válido. Debe ser 'carrera', 'departamento' o 'instituto'."}, status=status.HTTP_400_BAD_REQUEST)

        # Obtener el campo a usar según el nivel
        campo = nivel  # Asumimos que nivel y campo coinciden

        # Llamar al servicio para generar el reporte
        try:
            reporte = ReporteService.generar_reporte(nivel, referencia_ids, usuario, campo)
            return Response({
                "message": "Reporte generado exitosamente.",
                "reporte_id": reporte.id,
                "nivel": nivel,
                #"promedio": reporte.promedio,
                "fortalezas": reporte.texto_fortalezas,
                "oportunidades": reporte.texto_oportunidades
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
class ProcesarCuestionariosView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        usuario = request.user

        # Pasar el request a procesar_cuestionarios
        resultado = procesar_cuestionarios(usuario, request)

        if "error" in resultado:
            return Response(resultado, status=status.HTTP_400_BAD_REQUEST)

        return Response(resultado, status=status.HTTP_200_OK)

""" class CalcularDatosView(APIView):
    def post(self, request):
        
        Calcula y guarda los promedios jerárquicos en la base de datos.
        
        resultados = calcular_scores_jerarquicos()

        # Guardar resultados en la base de datos
        for nivel, datos_nivel in resultados.items():
            for grupo_nombre, indicadores in datos_nivel.items():
                grupo = Group.objects.get(name=grupo_nombre)  # Buscar el grupo por nombre
                for indicador, promedio in indicadores.items():
                    IndicadorPromedio.objects.update_or_create(
                        nivel=nivel,
                        grupo=grupo,
                        indicador=indicador,
                        defaults={'promedio': promedio}
                    )

        return Response({"message": "Datos calculados y almacenados correctamente."}, status=status.HTTP_200_OK)
 """
class CalcularDatosTutorView(APIView):
    def post(self, request):
        """
        Calcula y guarda los promedios para tutores en la base de datos.
        """
        resultados = calcular_scores_tutor()
        return Response({"message": "Datos de tutores calculados y almacenados.", "resultados": resultados}, status=status.HTTP_200_OK)

class CalcularDatosJerarquicosView(APIView):
    def post(self, request):
        """
        Calcula y guarda los promedios jerárquicos en la base de datos.
        """
        resultados = calcular_scores_jerarquicos()
        return Response({"message": "Datos jerárquicos calculados y almacenados.", "resultados": resultados}, status=status.HTTP_200_OK)
