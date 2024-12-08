# app/utils.py

from .models import IndicadorPromedio
from django.contrib.auth.models import Group
from .models import CustomUser, Carrera, Departamento, ScoreIndicador

def calcular_promedios_indicadores(scores):
    """
    Calcula el promedio de los indicadores basado en los scores.
    """
    indicadores = {}
    for score in scores:
        indicador = score.indicador.nombre
        if indicador not in indicadores:
            indicadores[indicador] = []
        indicadores[indicador].append(score.score)

    # Calcular promedios
    return {indicador: sum(valores) / len(valores) for indicador, valores in indicadores.items()}

def combinar_promedios(datos_nivel, grupos):
    """
    Combina los promedios de los indicadores a nivel superior.
    """
    promedios_acumulados = {}
    for grupo in grupos:
        if grupo.nombre in datos_nivel:
            promedios = datos_nivel[grupo.nombre]
            for indicador, valor in promedios.items():
                if indicador not in promedios_acumulados:
                    promedios_acumulados[indicador] = []
                promedios_acumulados[indicador].append(valor)

    # Promediar los valores acumulados
    return {indicador: sum(valores) / len(valores) for indicador, valores in promedios_acumulados.items()}

def calcular_scores_tutor():
    """
    Calcula los scores de los indicadores para cada tutor.
    """
    tutores = CustomUser.objects.filter(groups__name="Tutor")
    resultados = {}

    for tutor in tutores:
        indicadores = ScoreIndicador.objects.filter(usuario=tutor)
        promedios = calcular_promedios_indicadores(indicadores)

        for indicador, promedio in promedios.items():
            IndicadorPromedio.objects.update_or_create(
                nivel="tutor",
                grupo=None,
                indicador=indicador,
                defaults={'promedio': promedio}
            )
        resultados[tutor.username] = promedios

    return resultados

def calcular_scores_jerarquicos():
    """
    Calcula los scores de los indicadores jerárquicamente desde Carrera hasta Nación.
    """
    resultados = {}

    # Nivel Carrera
    carreras = Carrera.objects.all()
    resultados['carrera'] = {}
    for carrera in carreras:
        indicadores = ScoreIndicador.objects.filter(usuario__carrera=carrera)
        promedios = calcular_promedios_indicadores(indicadores)
        for indicador, promedio in promedios.items():
            IndicadorPromedio.objects.update_or_create(
                nivel="carrera",
                grupo=Group.objects.get(name=f"Carrera - {carrera.nombre}"),
                indicador=indicador,
                defaults={'promedio': promedio}
            )
        resultados['carrera'][carrera.nombre] = promedios

    # Repetir para otros niveles...
    departamentos = Departamento.objects.all()
    resultados['departamento'] = {}
    for departamento in departamentos:
        carreras_departamento = Carrera.objects.filter(departamento=departamento)
        promedios_acumulados = combinar_promedios(resultados['carrera'], carreras_departamento)
        for indicador, promedio in promedios_acumulados.items():
            IndicadorPromedio.objects.update_or_create(
                nivel="departamento",
                grupo=Group.objects.get(name=f"Departamento - {departamento.nombre}"),
                indicador=indicador,
                defaults={'promedio': promedio}
            )
        resultados['departamento'][departamento.nombre] = promedios_acumulados
        
    
    return resultados
