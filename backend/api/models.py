# backend/api/models.py
from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=255)
    correo_alternativo = models.EmailField()
    carrera = models.ForeignKey('Carrera', on_delete=models.SET_NULL, null=True)

class Instituto(models.Model):
    cve_inst = models.AutoField(primary_key=True)
    nombre_completo = models.CharField(max_length=255)
    federal = models.BooleanField()
    ruta = models.CharField(max_length=255)  

#

class Departamento(models.Model):
    cve_depto = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=255)
    jefe = models.CharField(max_length=255)
    #llave forarea a departamento


#apuntes
#programa educativo 
#cambiaron a plan de estudios = a carrera

class Carrera(models.Model):
    cve_carrera = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=255)
    departamento = models.ForeignKey(Departamento, on_delete=models.CASCADE)
    instituto = models.ForeignKey(Instituto, on_delete=models.CASCADE)

class Cuestionario(models.Model):
    cve_cuestionario = models.AutoField(primary_key=True)
    nombre_corto = models.CharField(max_length=255)
    nombre_largo = models.CharField(max_length=255)
    observaciones = models.TextField()

class Pregunta(models.Model):
    cve_pregunta = models.AutoField(primary_key=True)
    texto_pregunta = models.TextField()
    cuestionario = models.ForeignKey(Cuestionario, on_delete=models.CASCADE)
    cve_const1 = models.ForeignKey('Constructo', on_delete=models.SET_NULL, null=True, related_name='const1')
    cve_const2 = models.ForeignKey('Constructo', on_delete=models.SET_NULL, null=True, related_name='const2')
    cve_const3 = models.ForeignKey('Constructo', on_delete=models.SET_NULL, null=True, related_name='const3')
    cve_const4 = models.ForeignKey('Constructo', on_delete=models.SET_NULL, null=True, related_name='const4')
    #aqui debe estar el signo 

class Constructo(models.Model):
    cve_const = models.AutoField(primary_key=True)
    descripcion = models.TextField()
    signo = models.CharField(max_length=10)
    acronimo = models.CharField(max_length=10)
    #indicador - 
    #macrocompetencia


class TipoRespuesta(models.Model):
    cve_respuesta = models.AutoField(primary_key=True)
    descripcion = models.CharField(max_length=255)

class Respuesta(models.Model):
    id_resp = models.AutoField(primary_key=True)
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE)
    cve_aplic = models.ForeignKey('DatosAplicacion', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    valor = models.TextField()

class DatosAplicacion(models.Model):
    cve_aplic = models.AutoField(primary_key=True)
    fecha = models.DateField()
    hora = models.TimeField()
    cuestionario = models.ForeignKey(Cuestionario, on_delete=models.CASCADE)
    observaciones = models.TextField()

class ScoreAplicacion(models.Model):
    cve_score = models.AutoField(primary_key=True)
    cve_aplic = models.ForeignKey(DatosAplicacion, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total = models.FloatField()

#tabla - 2 que determinen el contructo y el indicador y 2 que almacenen el score de cada uno 

#apuntes
# passrte  la vista (dep, retro , user )y los indicadores, 
# front retorn score 


#score de cada constructo relacionado con 
class RetroChatGPT(models.Model): 
    #se relaciona con un usuario 
    cve_retro = models.AutoField(primary_key=True)
    cve_score = models.ForeignKey(ScoreAplicacion, on_delete=models.CASCADE)
    texto1 = models.TextField()
    #texto2 = models.TextField() #deberia ser uno nadamas 
    #texto3 = models.TextField()




""" class Reporte(models.Model):
    cve_reporte = models.AutoField(primary_key=True)
    cve_aplic = models.ForeignKey(DatosAplicacion, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total = models.FloatField()
    fecha = models.DateField()
    hora = models.TimeField()
    observaciones = models.TextField() 
    #agregar un campo de observaciones """