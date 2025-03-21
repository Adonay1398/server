from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from api.views import *
from api.mails import activar_cuenta

# ==========================
# SWAGGER CONFIGURATION
# ==========================
schema_view = get_schema_view(
    openapi.Info(
        title="API Documentation",
        default_version='v1',
        description="Documentation for API endpoints.",
        contact=openapi.Contact(email="Luisbasket1398@gmail.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),


)

# ==========================
# URL PATTERNS
# ==========================
urlpatterns = [
    
    
    #jerarquia
    #path('jerarquia/', JerarquiaView.as_view(), name='jerarquia'),

    # Admin
    path('admin/', admin.site.urls),

    # Authentication
    path("api/token/", CustomTokenObtainPairView.as_view(), name="get_token"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="refresh"),
    path("api-auth/", include("rest_framework.urls")),
    path('activar/', ActivarCuentaView.as_view(), name='activar_cuenta'),

    # User Management
    path("api/create-coordinador/",CreateCooridnadorsView.as_view(), name="create_user"),
    path("api/create-tutor/", CreateTutorView.as_view(), name="register_user"),
    path('users/', CustomUserListView.as_view(), name='user-list'),
    path('user/personal-info/', CustomUserDetailView.as_view(), name='user-detail'),
    path('api/user-related-data-retro/<int:Cuestionario_id>/<int:aplicacion_id>/', UserRelatedDataRetroView.as_view(), name='user-related-data'),
    #path('user/related-data-reporte/', UserDataReporteView.as_view(), name='user-related-data'),
    path('api/reporte-aplicacion/<int:cve_aplic>/<str:tipo>/<int:valor>/', ReportePorAplicacionArgumento4View.as_view(), name='reporte-por-aplicacion-argumento'),
    path('api/reporte-aplicacion/<int:cve_aplic>/',ReportePorAplicacionArgumento4View.as_view(),name='reporte_por_aplicacion'),
    #path('api/reportes/aplicacion/<int:cve_aplic>/<str:tipo>/<int:valor>/',ReportePorAplicacionArgumentoView.as_view(),name='reporte_por_aplicacion_con_filtro'),
    path("api/informacion-jerarquica/", ObtenerInformacionJerarquica.as_view(), name="informacion_jerarquica"),
    #path("reportes/<int:cve_aplic>/<str:jerarquia>/<str:valor>/", ReportePorArgumentosView.as_view(), name="filtrar_reportes"),
    #path('reportes1/<int:cve_aplic>/<str:tipo>/<int:valor>/', ReportePorAplicacionArgumentoView.as_view(), name='reporte-aplicacion-argumento'),
    path('usuarios/<int:pk>/relacion/', UserRelationUpdateAPIView.as_view(), name='user-relation-update'),

    # Cuestionarios
    path('cuestionario/', CuestionarioListView.as_view(), name='cuestionario-list'),
    path('preguntas/', PreguntaView.as_view(), name='preguntas-por-cuestionario'),
    #path('generate/', GenerateScoresView.as_view(), name='generate-score'),
    path('api/cuestionarios/status/', CuestionarioStatusView.as_view(), name='cuestionario-status'),
    # Constructos and Scores
    #path('constructo/', ConstructoListViews.as_view(), name='constructo-list'),
    #path('constructo/<int:pk>/', ConstructoDetailViews.as_view(), name='constructo-detail'),
    #path('score-constructo/', ScoreConstructoListViews.as_view(), name='score-constructo-list'),
    #path('score-indicador/', ScoreIndicadorListViews.as_view(), name='score-indicador-list'),

    # Responses
    #path('store-responses/', StoreResponsesView.as_view(), name='store-responses'),
    path('responder-pregunta/', ResponderPreguntaView.as_view(), name='responder-pregunta'),
    path('institutos-carreras/', InstitutoCarrerasView.as_view(), name='institutos-carreras'),
    path('api/cascade-upload/', CascadeUploadView.as_view(), name='cascade-upload'),
    #path('api/register/', UserRegistrationAPIView.as_view(), name='user-registration'),

    path('api/relacion-cuestionario-aplicacion/', RelacionCuestionarioAplicacionView.as_view(), name='relacion-cuestionario-aplicacion'),

    #path('api/niveles/', NavegarNivelesAPIView.as_view(), name='navegar-niveles'),
    path('crear-aplicacion/', crear_aplicacionView.as_view(), name='crear_aplicacion'),

    path('listar-aplicaciones/', ListarAplicacionesView.as_view(), name='listar-aplicaciones'),
    path('api/asignar-aplicacion/', AsignarCuestionarioUsuarioView.as_view(), name='asignar-cuestionario'),
    path('api/asignar-aplicacion-grupo/', AsignarCuestionarioGrupoView.as_view(), name='asignar-cuestionario-grupo'),
    path('api/cerrar-aplicacion-cuestionario/', CerrarAplicacionCuestionarioView.as_view(), name='cerrar-aplicacion-cuestionario'),
    #path('api/generar-reporte/', GenerarReporteAPIView.as_view(), name='generar-reporte'),
    #path('procesar-cuestionarios/', ProcesarCuestionariosView.as_view(), name='procesar_cuestionarios'),
    #path('calcular-datos-tutor/', CalcularDatosTutorView.as_view(), name='calcular_datos_tutor'),
    #}path('consulta-jerarquica/', ConsultaJerarquicaView.as_view(), name='calcular_datos_jerarquicos'),
    # API Documentation
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
] 
    #path("api/create-user/", CreateUserView.as_view(), name="create_user"),

    #path('user/<int:user_id>/score-constructo/', UserScoreConstructoListView.as_view(), name='user-score-constructo-list'),
    #path('user/<int:user_id>/score-indicador/', UserScoreIndicadorListView.as_view(), name='user-score-indicador-list'),

    #path('cuestionario/<int:pk>/', CuestionarioDetailView.as_view(), name='cuestionario-detail'),
    #path('cuestionario/<int:pk>/preguntas/', PreguntasPorCuestionarioView.as_view(), name='preguntas-por-cuestionario'),
    #path('score-constructo/<int:pk>/', ScoreConstructoDetailViews.as_view(), name='score-constructo-detail'),


    #path('score-indicador/<int:pk>/', ScoreIndicadorDetailViews.as_view(), name='score-indicador-detail'),

    #path('respuestas/<int:usuario_id>/<int:cuestionario_id>/', RespuestasUsuarioCuestionarioView.as_view(), name='respuestas-usuario-cuestionario'),

    #path('group/national/indicador-score/', NationalCoordinatorView.as_view(), name='national-indicador-score'),
    #path('group/regional/indicador-score/', RegionalCoordinatorView.as_view(), name='regional-indicador-score'),
    #path('group/institute/indicador-score/', InstituteCoordinatorView.as_view(), name='institute-indicador-score'),
    #path('group/department/indicador-score/', DepartmentCoordinatorView.as_view(), name='department-indicador-score'),
    #path('group/<str:group_name>/indicador-score/', GroupIndicadorScoreView.as_view(), name='group-indicador-score'),