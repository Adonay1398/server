# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class ApiCarrera(models.Model):
    cve_carrera = models.AutoField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=255)
    departamento = models.ForeignKey('ApiDepartamento', models.DO_NOTHING)
    instituto = models.ForeignKey('ApiInstituto', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'api_carrera'


class ApiConstructo(models.Model):
    cve_const = models.AutoField(primary_key=True)
    descripcion = models.TextField(unique=True)
    signo = models.CharField(max_length=10)
    acronimo = models.CharField(max_length=10)
    indicador = models.ForeignKey('ApiIndicador', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'api_constructo'


class ApiCuestionario(models.Model):
    cve_cuestionario = models.AutoField(primary_key=True)
    nombre_corto = models.CharField(unique=True, max_length=255)
    nombre_largo = models.CharField(max_length=255)
    observaciones = models.TextField(blank=True, null=True)
    is_active = models.BooleanField()
    fecha_fin = models.DateField(blank=True, null=True)
    fecha_inicio = models.DateField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'api_cuestionario'


class ApiCustomuser(models.Model):
    id = models.BigAutoField(primary_key=True)
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()
    fecha_nacimiento = models.DateField(blank=True, null=True)
    carrera = models.ForeignKey(ApiCarrera, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'api_customuser'


class ApiCustomuserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    customuser = models.ForeignKey(ApiCustomuser, models.DO_NOTHING)
    group = models.ForeignKey('AuthGroup', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'api_customuser_groups'
        unique_together = (('customuser', 'group'),)


class ApiCustomuserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    customuser = models.ForeignKey(ApiCustomuser, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'api_customuser_user_permissions'
        unique_together = (('customuser', 'permission'),)


class ApiDatosaplicacion(models.Model):
    cve_aplic = models.AutoField(primary_key=True)
    fecha = models.DateField()
    hora = models.TimeField()
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'api_datosaplicacion'


class ApiDatosaplicacionCuestionario(models.Model):
    id = models.BigAutoField(primary_key=True)
    datosaplicacion = models.ForeignKey(ApiDatosaplicacion, models.DO_NOTHING)
    cuestionario = models.ForeignKey(ApiCuestionario, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'api_datosaplicacion_cuestionario'
        unique_together = (('datosaplicacion', 'cuestionario'),)


class ApiDepartamento(models.Model):
    cve_depto = models.AutoField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=255)
    jefe = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'api_departamento'


class ApiIndicador(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=255)

    class Meta:
        managed = False
        db_table = 'api_indicador'


class ApiIndicadorconstructo(models.Model):
    id = models.BigAutoField(primary_key=True)
    constructo = models.ForeignKey(ApiConstructo, models.DO_NOTHING)
    indicador = models.ForeignKey(ApiIndicador, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'api_indicadorconstructo'


class ApiIndicadorpromedio(models.Model):
    id = models.BigAutoField(primary_key=True)
    nivel = models.CharField(max_length=20)
    indicador = models.CharField(max_length=255)
    promedio = models.FloatField()
    fecha_actualizacion = models.DateTimeField()
    grupo = models.ForeignKey('AuthGroup', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'api_indicadorpromedio'
        unique_together = (('nivel', 'grupo', 'indicador'),)


class ApiInstituto(models.Model):
    cve_inst = models.AutoField(primary_key=True)
    nombre_completo = models.CharField(unique=True, max_length=255)
    tipo = models.CharField(max_length=10)
    ruta = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'api_instituto'


class ApiPregunta(models.Model):
    id_pregunta = models.AutoField(primary_key=True)
    cve_pregunta = models.CharField(unique=True, max_length=255)
    texto_pregunta = models.TextField()
    scorekey = models.TextField()  # This field type is a guess.
    cuestionario = models.ForeignKey(ApiCuestionario, models.DO_NOTHING)
    cve_const1 = models.ForeignKey(ApiConstructo, models.DO_NOTHING, blank=True, null=True)
    cve_const2 = models.ForeignKey(ApiConstructo, models.DO_NOTHING, related_name='apipregunta_cve_const2_set', blank=True, null=True)
    cve_const3 = models.ForeignKey(ApiConstructo, models.DO_NOTHING, related_name='apipregunta_cve_const3_set', blank=True, null=True)
    cve_const4 = models.ForeignKey(ApiConstructo, models.DO_NOTHING, related_name='apipregunta_cve_const4_set', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'api_pregunta'


class ApiReporte(models.Model):
    id = models.BigAutoField(primary_key=True)
    nivel = models.CharField(max_length=15)
    referencia_id = models.IntegerField()
    texto_fortalezas = models.TextField(blank=True, null=True)
    texto_oportunidades = models.TextField(blank=True, null=True)
    fecha_generacion = models.DateTimeField()
    usuario_generador = models.ForeignKey(ApiCustomuser, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'api_reporte'
        unique_together = (('nivel', 'referencia_id', 'fecha_generacion'),)


class ApiRespuesta(models.Model):
    cve_resp = models.AutoField(primary_key=True)
    valor = models.IntegerField()
    cve_aplic = models.ForeignKey(ApiDatosaplicacion, models.DO_NOTHING)
    pregunta = models.ForeignKey(ApiPregunta, models.DO_NOTHING)
    user = models.ForeignKey(ApiCustomuser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'api_respuesta'


class ApiRetrochatgpt(models.Model):
    cve_retro = models.AutoField(primary_key=True)
    texto1 = models.TextField()
    texto2 = models.TextField(blank=True, null=True)
    texto3 = models.TextField(blank=True, null=True)
    pdf_file = models.CharField(max_length=100, blank=True, null=True)
    usuario = models.ForeignKey(ApiCustomuser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'api_retrochatgpt'


class ApiScoreaplicacion(models.Model):
    cve_score = models.AutoField(primary_key=True)
    total = models.FloatField()
    cve_aplic = models.ForeignKey(ApiDatosaplicacion, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'api_scoreaplicacion'


class ApiScoreaplicacionUser(models.Model):
    id = models.BigAutoField(primary_key=True)
    scoreaplicacion = models.ForeignKey(ApiScoreaplicacion, models.DO_NOTHING)
    customuser = models.ForeignKey(ApiCustomuser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'api_scoreaplicacion_user'
        unique_together = (('scoreaplicacion', 'customuser'),)


class ApiScoreconstructo(models.Model):
    cve_scoreconstructo = models.AutoField(db_column='cve_scoreConstructo', primary_key=True)  # Field name made lowercase.
    score = models.IntegerField()
    aplicacion = models.ForeignKey(ApiDatosaplicacion, models.DO_NOTHING)
    constructo = models.ForeignKey(ApiConstructo, models.DO_NOTHING)
    usuario = models.ForeignKey(ApiCustomuser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'api_scoreconstructo'


class ApiScoreindicador(models.Model):
    cve_scoreindicador = models.AutoField(db_column='cve_ScoreIndicador', primary_key=True)  # Field name made lowercase.
    score = models.IntegerField()
    aplicacion = models.ForeignKey(ApiDatosaplicacion, models.DO_NOTHING)
    indicador = models.ForeignKey(ApiIndicador, models.DO_NOTHING)
    usuario = models.ForeignKey(ApiCustomuser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'api_scoreindicador'


class ApiScoreindicadorConstructos(models.Model):
    id = models.BigAutoField(primary_key=True)
    scoreindicador = models.ForeignKey(ApiScoreindicador, models.DO_NOTHING)
    scoreconstructo = models.ForeignKey(ApiScoreconstructo, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'api_scoreindicador_constructos'
        unique_together = (('scoreindicador', 'scoreconstructo'),)


class ApiTiporespuesta(models.Model):
    cve_respuesta = models.AutoField(primary_key=True)
    descripcion = models.CharField(unique=True, max_length=255)

    class Meta:
        managed = False
        db_table = 'api_tiporespuesta'


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.SmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(ApiCustomuser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'
