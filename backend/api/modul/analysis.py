from collections import defaultdict
import json
from api.models import *
from api.utils import calculate_construct_score 
from .openAI import make_analysis
from api.models import ScoreIndicador
#from api.modul import calculate_score
from celery import shared_task


def obtener_nivel_jerarquico(usuario):
    """
    Obtiene el nivel jerárquico del usuario según su grupo.
    """
    if usuario.groups.filter(name="Coordinador Nacional").exists():
        return "nacional"
    elif usuario.groups.filter(name="Coordinador Región").exists():
        return "region"
    elif usuario.groups.filter(name="Coordinador Institución").exists():
        return "institucion"
    elif usuario.groups.filter(name="Coordinador Departamento").exists():
        return "departamento"
    elif usuario.groups.filter(name="Coordinador Carrera").exists():
        return "carrera"
    elif usuario.groups.filter(name="Tutor").exists():
        return "tutor"
    return None

def filtrar_datos_por_nivel(usuario, datos, nivel):
    """
    Filtra los datos de indicadores según el nivel jerárquico del usuario.

    Args:
        usuario (CustomUser): Usuario autenticado.
        datos (list): Datos de indicadores.
        nivel (str): Nivel jerárquico del usuario.

    Returns:
        list: Datos filtrados según el nivel del usuario.
    """
    # Implementar la lógica de filtrado según el nivel
    if nivel == "nacional":
        return datos  # Nacional ve todo
    elif nivel == "region":
        return [d for d in datos if d["region_id"] == usuario.region_id]
    elif nivel == "institucion":
        return [d for d in datos if d["institucion_id"] == usuario.institucion_id]
    elif nivel == "departamento":
        return [d for d in datos if d["departamento_id"] == usuario.departamento_id]
    elif nivel == "carrera":
        return [d for d in datos if d["carrera_id"] == usuario.carrera_id]
    elif nivel == "tutor":
        return [d for d in datos if d["tutor_id"] == usuario.id]
    return []

def tiene_acceso_a_cuestionario(usuario, cuestionario, nivel):
    """
    Verifica si el usuario tiene acceso al cuestionario.

    Args:
        usuario (CustomUser): Usuario autenticado.
        cuestionario (Cuestionario): Cuestionario a verificar.
        nivel (str): Nivel jerárquico del usuario.

    Returns:
        bool: True si tiene acceso, False si no.
    """
    if nivel == "nacional":
        return True
    elif nivel == "region":
        return cuestionario.region_id == usuario.region_id
    elif nivel == "institucion":
        return cuestionario.institucion_id == usuario.institucion_id
    elif nivel == "departamento":
        return cuestionario.departamento_id == usuario.departamento_id
    elif nivel == "carrera":
        return cuestionario.carrera_id == usuario.carrera_id
    elif nivel == "tutor":
        return cuestionario.tutor_id == usuario.id
    return False


@shared_task
def calcular_scores(usuario, aplicacion, cuestionario):
    """
    Calcula los scores de constructos e indicadores para un usuario.

    Args:
        usuario: Usuario para el que se calculan los scores.

    Returns:
        tuple: Scores de constructos, scores de indicadores, y el reporte generado.
        
    """

    try:
        # Obtener respuestas del usuario

        respuestas = Respuesta.objects.filter(user=usuario)
        
        print('ok-0')
        if not respuestas.exists():
            raise ValueError("No se encontraron respuestas asociadas para el usuario.")

        # Agrupar respuestas por constructo
        respuestas_por_constructo = defaultdict(list)
        for respuesta in respuestas:
            if respuesta.pregunta.cve_const1:
                respuestas_por_constructo[respuesta.pregunta.cve_const1].append(respuesta.valor)
        print("ok")
        # Calcular scores normalizados por constructo
        scores_constructos = {}
        for constructo, valores in respuestas_por_constructo.items():
            normalized_score = calculate_construct_score(valores)
            scores_constructos[constructo] = normalized_score

            # Guardar scores en la base de datos
            ScoreConstructo.objects.update_or_create( 
                usuario=usuario,
                constructo=constructo,
                aplicacion = aplicacion,
                defaults={"score": normalized_score}
                
            )
        print("ok2")
        # Agrupar por indicadores y calcular promedios
        indicadores = defaultdict(list)
        for constructo, score in scores_constructos.items():
            if not isinstance(constructo, Constructo):
                raise ValueError(f"'{constructo}' no es una instancia válida de Constructo.")
            for indicador in constructo.indicadores_set.all():
                indicadores[indicador.nombre].append(score)
        print("ok3")
        scores_indicadores = {
            indicador: sum(scores) / len(scores)
            for indicador, scores in indicadores.items()
        }
        print("ok4")
        # Guardar scores de indicadores
        for indicador, promedio in scores_indicadores.items():
            indicador_obj = Indicador.objects.get(nombre=indicador)
            ScoreIndicador.objects.update_or_create(
                usuario=usuario,
                indicador=indicador_obj,
                aplicacion = aplicacion,
                defaults={"score": promedio}
            )
        print("ok5")    
        # Preparar datos para make_analysis
        datos_indicadores = {
            "indicador": [{"nombre": k, "prom_score": v} for k, v in scores_indicadores.items()]
        }
        print("ok6")
        # Generar el reporte
        
        
        reporte = make_analysis(
            data=datos_indicadores,
            report='retroalimentación',
            referencia='indicador'
        )
        print("ok7")
        # Convertir el JSON a texto y dividirlo en texto1 y texto2
        # Buscar "fortaleza" y "oportunidad" usando find
        
        texto1 = reporte.get("fortaleza", "").strip() 
        texto2 = reporte.get("oportunidad", "").strip()
        
        if not texto1 or not texto2:
            raise ValueError("El reporte no contiene claves válidas de 'fortaleza' u 'oportunidad'.")

    
        print("ok8")
        # Guardar el reporte en RetroChatGPT
        try:
                RetroChatGPT.objects.update_or_create(
                    usuario=usuario,
                    aplicacion_id=aplicacion.cve_aplic,
                    Cuestionario_id = cuestionario.cve_cuestionario,
                    texto1=texto1,
                    texto2=texto2
                )
        except Exception as e:
            print(f"Error al guardar el reporte en RetroChatGPT: {e}")
        
        print("ok9")
        # Debugging: Mostrar resultados
        """ print(f"Scores de Constructos: {scores_constructos}")
        print(f"Scores de Indicadores: {scores_indicadores}")
        print(f"Reporte generado: {reporte}") """
        #print("ok10")
        return  scores_constructos, scores_indicadores, reporte

    except Exception as e:
        print(f"Error al calcular los scores o generar el reporte: {e}")
        raise
