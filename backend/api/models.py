from django.db import models
from django.contrib.auth.models import AbstractUser, Group
from datetime import date
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.utils import timezone
from django.db.models import JSONField

class Region (models.Model):
    cve_region = models.AutoField(primary_key=True)
    #instituto = models.ForeignKey(Instituto, on_delete=models.CASCADE,related_name="regiones")
    nombre = models.CharField(max_length=255, unique=True)  # Avoid duplicate region names
    jefe = models.CharField(max_length=255, blank=True, null=True)  # Optional field for jefe
    
    def __str__(self):
        return self.nombre
class Instituto(models.Model):
    FEDERAL = 'federal'
    RURAL = 'rural'
    ESTATAL = 'estatal'

    TIPO_INSTITUTO_CHOICES = [
        (FEDERAL, 'Federal'),
        (RURAL, 'Rural'),
        (ESTATAL, 'Estatal'),
    ]

    cve_inst = models.AutoField(primary_key=True)
    nombre_completo = models.CharField(max_length=255, unique=True)  # Unique for better integrity
    tipo = models.CharField(max_length=10, choices=TIPO_INSTITUTO_CHOICES, default=FEDERAL)
    ruta = models.CharField(max_length=255, blank=True, null=True)  # Allow optional paths
    #departamento = models.ForeignKey('Departamento', on_delete=models.CASCADE, blank=True, null=True)
    region = models.ForeignKey(Region, on_delete=models.CASCADE, blank=True, null=True,related_name="institutos")
    def __str__(self):
        return self.nombre_completo


class Departamento(models.Model):
    cve_depto = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=255, unique=True)  # Avoid duplicate department names
    jefe = models.CharField(max_length=255, blank=True, null=True)  # Optional field for jefe
    #carrera = models.ForeignKey('Carrera', on_delete=models.CASCADE)
    instituto = models.ForeignKey(Instituto, on_delete=models.CASCADE, related_name="departamentos")
    def __str__(self):
        return self.nombre  


class Carrera(models.Model):
    cve_carrera = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=255, unique=True)  # Unique career names
    departamento = models.ForeignKey(Departamento, on_delete=models.CASCADE,related_name="carreras")
    #instituto = models.ForeignKey(Instituto, on_delete=models.CASCADE)

    def __str__(self):
        return self.nombre


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True, verbose_name="Correo Electrónico")
    username = models.CharField(
        max_length=150, unique=True, blank=True, null=True
    )
    fecha_nacimiento = models.DateField(null=True, blank=True)
    carrera = models.ForeignKey(Carrera, on_delete=models.SET_NULL, null=True, blank=True)
    aplicacion = models.ForeignKey('DatosAplicacion', on_delete=models.SET_NULL, null=True, blank=True)
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='customuser_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='customuser_permissions_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )
    USERNAME_FIELD = 'email'  # El campo usado para autenticación
    REQUIRED_FIELDS = []  # No requiere otros campos adicionales
    


class Cuestionario(models.Model):
        
        cve_cuestionario = models.AutoField(primary_key=True)
        nombre_corto = models.CharField(max_length=255, unique=True)  # Unique identifier
        nombre_largo = models.CharField(max_length=255)
        observaciones = models.TextField(blank=True, null=True)
        is_active = models.BooleanField(default=True)
        completado = models.BooleanField(default=False)
        fecha_inicio = models.DateField(null=True, blank=True)  # Fecha de inicio opcional
        fecha_fin = models.DateField(null=True, blank=True)  # Fecha límite opcional
        
        def __str__(self):
            return self.nombre_corto


class Constructo(models.Model):
    cve_const = models.AutoField(primary_key=True)
    descripcion = models.TextField(unique=True)  # Avoid duplicate constructs
    indicador = models.ForeignKey('Indicador', on_delete=models.CASCADE, null=True, blank=True)
    signo = models.CharField(max_length=10)
    acronimo = models.CharField(max_length=10, default='DEFAULT')

    def __str__(self):
        return self.descripcion


class Pregunta(models.Model):
    id_pregunta = models.AutoField(primary_key=True)
    cve_pregunta = models.CharField(max_length=255, unique=True)  # Use CharField for identifiers
    texto_pregunta = models.TextField()
    cuestionario = models.ForeignKey(Cuestionario, related_name='preguntas', on_delete=models.CASCADE)
    cve_const1 = models.ForeignKey(Constructo, on_delete=models.SET_NULL, null=True, blank=True, related_name='preguntas_const1')
    cve_const2 = models.ForeignKey(Constructo, on_delete=models.SET_NULL, null=True, blank=True, related_name='preguntas_const2')
    cve_const3 = models.ForeignKey(Constructo, on_delete=models.SET_NULL, null=True, blank=True, related_name='preguntas_const3')
    cve_const4 = models.ForeignKey(Constructo, on_delete=models.SET_NULL, null=True, blank=True, related_name='preguntas_const4')
    scorekey = ArrayField(
        models.IntegerField(),
        default=list,
        blank=True
    )
    is_value = models.BooleanField(default=False)

    def __str__(self):
        return self.texto_pregunta


class TipoRespuesta(models.Model):
    cve_respuesta = models.AutoField(primary_key=True)
    descripcion = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.descripcion


class DatosAplicacion(models.Model):
    cve_aplic = models.AutoField(primary_key=True)
    fecha = models.DateField()
    hora = models.TimeField()
    cuestionario = models.ManyToManyField(Cuestionario, related_name='aplicaciones')
    observaciones = models.TextField(blank=True, null=True)
    fecha_inicion = models.DateField(null=True, blank=True)
    fecha_limite = models.DateField(null=True, blank=True)
    fecha_fin = models.DateField(null=True, blank=True)
    reporte_generado = models.BooleanField(default=False)
    nombre_aplicacion = models.TextField(blank=True, null=True, unique=True)

    def __str__(self):
        return f"Aplicación {self.cve_aplic} - {self.fecha}"


class Respuesta(models.Model):
    cve_resp = models.AutoField(primary_key=True)
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE)
    cve_aplic = models.ForeignKey(DatosAplicacion, on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    valor = models.IntegerField()

    def __str__(self):
        return f"Respuesta de {self.user} a {self.pregunta}"


class ScoreAplicacion(models.Model):
    cve_score = models.AutoField(primary_key=True)
    cve_aplic = models.ForeignKey(DatosAplicacion, on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser,on_delete=models.CASCADE)
    total = models.FloatField()

    def __str__(self):
        return f"Score {self.user} - {self.total}"


class ScoreConstructo(models.Model):
    cve_scoreConstructo = models.AutoField(primary_key=True)
    aplicacion = models.ForeignKey(DatosAplicacion, on_delete=models.CASCADE)
    usuario = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    constructo = models.ForeignKey(Constructo, on_delete=models.CASCADE)
    score = models.IntegerField()

    def __str__(self):
        return f"Score Constructo {self.constructo.descripcion} - {self.score}"


class Indicador(models.Model):
    nombre = models.CharField(max_length=255, unique=True)
    constructos = models.ManyToManyField('Constructo', through='IndicadorConstructo', related_name='indicadores_set')

    def __str__(self):
        return self.nombre


class IndicadorConstructo(models.Model):
    indicador = models.ForeignKey(Indicador, on_delete=models.CASCADE)
    constructo = models.ForeignKey(Constructo, on_delete=models.CASCADE)


class ScoreIndicador(models.Model):
    cve_ScoreIndicador = models.AutoField(primary_key=True)
    aplicacion = models.ForeignKey(DatosAplicacion, on_delete=models.CASCADE)
    usuario = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    indicador = models.ForeignKey(Indicador, on_delete=models.CASCADE)
    score = models.IntegerField()
    constructos = models.ManyToManyField(ScoreConstructo, related_name='indicadores', blank=True)

    def __str__(self):
        return f"Score Indicador {self.indicador.nombre} - {self.score}"


class RetroChatGPT(models.Model):
    cve_retro = models.AutoField(primary_key=True)
    aplicacion = models.ForeignKey(DatosAplicacion, on_delete=models.CASCADE)
    Cuestionario = models.ForeignKey(Cuestionario, on_delete=models.CASCADE)
    usuario = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    texto1 = models.TextField()  # Fortalezas
    texto2 = models.TextField(blank=True, null=True)  # Áreas de oportunidad
    texto3 = models.TextField(blank=True, null=True)  # Observaciones adicionales
    pdf_file = models.FileField(upload_to='pdf_files/', blank=True, null=True)  # Archivo PDF generado

    def __str__(self):
        return f"Retroalimentación para Usuario {self.usuario} - Score {self.cve_retro}"


class Reporte(models.Model):
    id = models.BigAutoField(primary_key=True)
    nivel = models.CharField(max_length=5)
    referencia_id = models.IntegerField(blank=True, null=True)
    texto_fortalezas = models.TextField(blank=True, null=True)
    texto_oportunidades = models.TextField(blank=True, null=True)
    fecha_generacion = models.DateTimeField(default=timezone.now)
    observaciones = models.TextField(blank=True, null=True)  # Asegúrate de que esta línea esté presente
    usuario_generador = models.ForeignKey(CustomUser, on_delete=models.CASCADE, blank=True, null=True)
    #promedio_indicadores = models.TextField(blank=True, null=True)
    #promedio_constructos = models.TextField(blank=True, null=True)
    datos_promedios = models.JSONField(blank=True, null=True)  # Para guardar los promedios calculados


    def __str__(self):
        return f"Reporte {self.id} - {self.fecha_generacion}"


class IndicadorPromedio(models.Model):
    NIVEL_CHOICES = [
        ('plan_estudios', 'Carrera'),
        ('departamento', 'Departamento'),
        ('instituto', 'Instituto'),
        ('region', 'Región'),
        ('nacion', 'Nación'),
    ]

    nivel = models.CharField(max_length=20, choices=NIVEL_CHOICES)
    grupo = models.ForeignKey(Group, on_delete=models.CASCADE)  # Relación con auth_group
    indicador =models.ForeignKey(Indicador, on_delete=models.CASCADE) # Nombre del indicador
    promedio = models.FloatField()  # Promedio calculado
    fecha_actualizacion = models.DateTimeField(auto_now=True)  # Fecha de actualización

    class Meta:
        unique_together = ('nivel', 'grupo', 'indicador')

    def __str__(self):
        return f"{self.nivel} - {self.grupo.name} - {self.indicador}: {self.promedio}"


class GrupoJerarquico(models.Model):
    grupo = models.OneToOneField(Group, on_delete=models.CASCADE, related_name="jerarquia")
    nivel = models.CharField(
        max_length=50,
        choices=[
            ("nacional", "Nivel Nacional"),
            ("region", "Nivel Región"),
            ("institucion", "Nivel Institución"),
            ("departamento", "Nivel Departamento"),
            ("plan_estudios", "Nivel Plan de Estudios"),
            ("tutores", "Nivel Tutores"),
        ]
    )
    parent_group = models.ForeignKey(
        Group, on_delete=models.SET_NULL, null=True, blank=True, related_name="subgrupos"
    )

    def __str__(self):
        return f"{self.grupo.name} ({self.nivel})"
    


class AsignacionCuestionario(models.Model):
    """
    Relación entre usuarios, cuestionarios y su aplicación.
    """
    usuario = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="asignaciones")
    cuestionario = models.ForeignKey(Cuestionario, on_delete=models.CASCADE, related_name="asignaciones")
    aplicacion = models.ForeignKey(DatosAplicacion, on_delete=models.CASCADE, related_name="asignaciones")
    completado = models.BooleanField(default=False)
    fecha_asignacion = models.DateField(auto_now_add=True)
    fecha_completado = models.DateField(blank=True, null=True)

    class Meta:
        unique_together = ('usuario', 'cuestionario', 'aplicacion')  # Evitar duplicados

    def __str__(self):
        return f"{self.usuario.username} - {self.cuestionario.nombre_corto} - Aplicación {self.aplicacion.cve_aplic}"
