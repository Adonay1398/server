from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings



class CustomUser(AbstractUser):
    #carrera = models.ForeignKey('Carrera', on_delete=models.SET_NULL, null=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    cve_carrera = models.ForeignKey('Carrera', on_delete=models.SET_NULL, null=True)
    def __str__(self):
        return self.username


""" class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=255)
    correo_alternativo = models.EmailField()
    carrera = models.ForeignKey('Carrera', on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.nombre """



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
    nombre_completo = models.CharField(max_length=255)
    tipo = models.CharField(max_length=10, choices=TIPO_INSTITUTO_CHOICES, default=FEDERAL)
    ruta = models.CharField(max_length=255)

    def __str__(self):
        return self.nombre_completo


class Departamento(models.Model):
    cve_depto = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=255)
    jefe = models.CharField(max_length=255)

    def __str__(self):
        return self.nombre


class Carrera(models.Model):
    cve_carrera = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=255)
    departamento = models.ForeignKey(Departamento, on_delete=models.CASCADE)
    instituto = models.ForeignKey('Instituto', on_delete=models.CASCADE)

    def __str__(self):
        return self.nombre


class Cuestionario(models.Model):
    cve_cuestionario = models.AutoField(primary_key=True)
    nombre_corto = models.CharField(max_length=255)
    nombre_largo = models.CharField(max_length=255)
    observaciones = models.TextField()

    def __str__(self):
        return self.nombre_corto


class Constructo(models.Model):
    cve_const = models.AutoField(primary_key=True)
    descripcion = models.TextField()
    signo = models.CharField(max_length=10)
    acronimo = models.CharField(max_length=10, default='DEFAULT')

    def __str__(self):
        return self.descripcion


class Pregunta(models.Model):
    cve_pregunta = models.AutoField(primary_key=True)
    texto_pregunta = models.TextField()
    cuestionario = models.ForeignKey(Cuestionario, on_delete=models.CASCADE)
    #cve_respuesta = models.ForeignKey('TipoRespuesta', on_delete=models.CASCADE)
    cve_const1 = models.ForeignKey(Constructo, on_delete=models.SET_NULL, null=True, related_name='const1')
    cve_const2 = models.ForeignKey(Constructo, on_delete=models.SET_NULL, null=True, related_name='const2')
    cve_const3 = models.ForeignKey(Constructo, on_delete=models.SET_NULL, null=True, related_name='const3')
    cve_const4 = models.ForeignKey(Constructo, on_delete=models.SET_NULL, null=True, related_name='const4')
    #checar
    def __str__(self):
        return self.texto_pregunta


class TipoRespuesta(models.Model):
    cve_respuesta = models.AutoField(primary_key=True)
    descripcion = models.CharField(max_length=255)
    
    def __str__(self):
        return self.descripcion




class DatosAplicacion(models.Model):
    cve_aplic = models.AutoField(primary_key=True)
    fecha = models.DateField()
    hora = models.TimeField()
    cuestionario = models.ManyToManyField(Cuestionario )
    observaciones = models.TextField()

    def __str__(self):
        return f"Aplicación {self.cve_aplic} - {self.fecha}"
    
class Respuesta(models.Model):
    cve_resp = models.AutoField(primary_key=True)
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE)
    cve_aplic = models.ForeignKey(DatosAplicacion, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    valor = models.TextField()

    def __str__(self):
        return f"Respuesta de {self.user} a {self.pregunta}"

class ScoreAplicacion(models.Model):
    cve_score = models.AutoField(primary_key=True)
    cve_aplic = models.ForeignKey(DatosAplicacion, on_delete=models.CASCADE)
    user = models.ManyToManyField(settings.AUTH_USER_MODEL)
    total = models.FloatField()

    def __str__(self):
        return f"Score {self.user} - {self.total}"

class ScoreConstructo(models.Model):
    cve_scoreConstructo = models.AutoField(primary_key=True)
    aplicacion = models.ForeignKey(DatosAplicacion, on_delete=models.CASCADE)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL , on_delete=models.CASCADE)
    constructo = models.ForeignKey(Constructo, on_delete=models.CASCADE)
    score = models.IntegerField()

    def __str__(self):
        return f"Score Constructo {self.constructo.descripcion} - {self.score}"

class Indicador(models.Model):
    nombre = models.CharField(max_length=255)
    constructos = models.ManyToManyField('Constructo', through='IndicadorConstructo')

    def __str__(self):
        return self.nombre
    
class IndicadorConstructo(models.Model):
    indicador = models.ForeignKey(Indicador, on_delete=models.CASCADE)
    constructo = models.ForeignKey(Constructo, on_delete=models.CASCADE)



class ScoreIndicador(models.Model):
    cve_ScoreIndicador = models.AutoField(primary_key=True)
    aplicacion = models.ForeignKey(DatosAplicacion, on_delete=models.CASCADE)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    indicador = models.ForeignKey(Indicador, on_delete=models.CASCADE)
    score = models.IntegerField()

    def __str__(self):
        return f"Score Indicador {self.indicador.nombre} - {self.score}"

class RetroChatGPT(models.Model):
    cve_retro = models.AutoField(primary_key=True)
    cve_score = models.ForeignKey(ScoreAplicacion, on_delete=models.CASCADE)
    texto1 = models.FileField(upload_to='csv_files/')
    texto2 = models.FileField(upload_to='csv_files/', blank=True, null=True)
    texto3 = models.FileField(upload_to='csv_files/', blank=True, null=True)


    def __str__(self):
        return f"Retroalimentación para Score {self.cve_score}"


class Reporte(models.Model):
    cve_reporte = models.AutoField(primary_key=True)
    cve_aplic = models.ForeignKey(DatosAplicacion, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    total = models.FloatField()
    fecha = models.DateField()
    hora = models.TimeField()
    texto = models.FileField(upload_to='csv_files/',default='csv_files/default.csv')
    observaciones = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Reporte {self.cve_reporte} - {self.fecha}"
    