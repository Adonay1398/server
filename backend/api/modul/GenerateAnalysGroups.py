import json
from django.contrib.auth.models import Group
from api.models import  AsignacionCuestionario, Constructo, Cuestionario, CustomUser, Departamento, Indicador, IndicadorPromedio, Region, Instituto, Carrera, Reporte, ScoreIndicador, ScoreConstructo
from api.modul.openAI import make_analysis
from django.utils.timezone import now


def obtener_tutores_por_grupo(usuario):
    """
    obtiene los tutores relacionados según su nivel jerárquico.

    Args:
        usuario (CustomUser): Usuario autenticado.

    Returns:
        QuerySet: CustomUseres relacionados con el grupo del usuario.
    """
    try:
        grupo = usuario.groups.first()

        if grupo.name == "Coordinador de Plan de Estudios":
            carrera = usuario.carrera
            tutores = CustomUser.objects.filter(carrera=carrera)
        
        elif grupo.name == "Coordinador de Tutorias por Departamento":
            departamento = usuario.carrera.departamento  # Suponiendo que el usuario tiene asignado un departamento
            tutores = CustomUser.objects.filter(carrera__departamento=departamento)

        elif grupo.name == "Coordinador de Tutorias por Institucion":
            institucion = usuario.carrera.departamento.instituto  # Relación indirecta desde el departamento
            tutores = CustomUser.objects.filter(carrera__departamento__instituto=institucion)

        elif grupo.name == "Coordinador de Tutorias a Nivel Regional":
            region = usuario.carrera.departamento.intituto.region  # Relación indirecta desde el departamento
            tutores = CustomUser.objects.filter(carrera__departamento__instituto__region=region)

        elif grupo.name == "Coordinador de Tutorias a Nivel Nacional":
            tutores = CustomUser.objects.filter(groups__name="Tutores")  # A nivel nacional, obtenemos todos los tutores
            
        else:
            raise ValueError("El grupo del usuario no está definido para esta operación.")
        """ elif grupo.name == "Tutores":
            tutores = CustomUser.objects.filter(user=usuario)  # Solo el tutor actual
        """
        
        

        return tutores

    except Exception as e:
        raise ValueError(f"Error al obtener tutores: {str(e)}")
    
    
    
    
from collections import defaultdict
from django.db import transaction

from collections import defaultdict
from django.db import transaction

def calcular_scores_tutores(tutores, aplicacion, cuestionario_id, usuario):
    """
    Calcula y guarda los promedios de constructos e indicadores para los tutores.

    Args:
        tutores (QuerySet): Tutores para los cuales se calculan los scores.
        aplicacion (DatosAplicacion): Aplicación actual.
        cuestionario_id (int): ID del cuestionario relacionado.
        usuario (CustomUser): Usuario que realiza la consulta.

    Returns:
        dict: Diccionario con los datos de constructos e indicadores y sus promedios.
    """
    resultados = []
    indicadores_totales = defaultdict(list)

    try:
        with transaction.atomic():  # Asegurar la consistencia en los datos
            for tutor in tutores:
                # Obtener scores de indicadores
                scores_indicadores = ScoreIndicador.objects.filter(
                    usuario=tutor,
                    aplicacion=aplicacion
                ).distinct()

                indicadores = [
                    {"indicador": score.indicador.nombre, "score": score.score}
                    for score in scores_indicadores
                ]

                # Acumular scores por indicador
                for score in scores_indicadores:
                    indicadores_totales[score.indicador.nombre].append(score.score)

                # Agregar datos individuales al resultado
                resultados.append({
                    "tutor": tutor.username,
                    "indicadores": indicadores,
                })

            # Guardar promedios de indicadores
            for indicador, scores in indicadores_totales.items():
                promedio = sum(scores) / len(scores)
                indicador_obj = Indicador.objects.get(nombre=indicador)

                # Determinar el nivel del usuario (por ejemplo, departamento)
                nivel = "departamento"
                grupo = usuario.groups.first()

                # Guardar en la tabla IndicadorPromedio
                IndicadorPromedio.objects.update_or_create(
                    nivel=nivel,
                    grupo=grupo,
                    indicador=indicador_obj,
                    defaults={"promedio": promedio}
                )

    except Exception as e:
        print(f"Error al calcular y guardar los promedios: {e}")
        raise

    return {
        "tutores": resultados,
        "promedios": {
            "indicadores": [
                {"nombre": indicador, "prom_score": sum(scores) / len(scores)}
                for indicador, scores in indicadores_totales.items()
            ]
        }
    }



def generar_reporte_por_grupo(usuario, aplicacion, cuestionario_id):
    """
    Genera un reporte para los tutores relacionados al grupo del usuario.

    Args:
        usuario (CustomUser): Usuario autenticado.
        aplicacion (DatosAplicacion): Aplicación actual.

    Returns:
        dict: Resultado del reporte generado.
    """
    try:
        # Obtener tutores según el grupo del usuario
        tutores = obtener_tutores_por_grupo(usuario)
        print("ok-grupo ")
        # Calcular los scores de los tutores
        datos_tutores = calcular_scores_tutores(tutores, aplicacion,cuestionario_id,usuario)
        print("ok-grupo -1")
        # Preparar datos para make_analysis
        data = {
            "indicador": [
                {"nombre": indicador["indicador"], "prom_score": indicador["score"]}
                for tutor in datos_tutores["tutores"]  # Acceder a la clave "tutores"
                for indicador in tutor["indicadores"]
    ]
}

        # Determinar el tipo de reporte según el grupo
        grupo = usuario.groups.first().name
        report = {
            "Coordinador de Tutorias por Departamento": "departamento",
            "Coordinador de Tutorias por Institucion": "institucional",
            "Coordinador de Tutorias a Nivel Regional": "regional",
            "Coordinador de Tutorias a Nivel Nacional": "nacional",
            "Tutores": "individual"
        }.get(grupo, "retroalimentación")
        print("ok-grupo 0")
        # Generar el reporte con make_analysis
        reporte = make_analysis(
            data=data,
            report=report,
            referencia="indicador"
        )
        
        print(dict(reporte))
        print("ok-grupo 2")
        # Convertir el reporte a texto y extraer información relevante
        #reporte_texto = json.dumps(reporte, ensure_ascii=False, indent=4)
        reporte_texto = json.dumps(reporte, ensure_ascii=False, indent=4)

        inicio_fortaleza = reporte_texto.find('"fortaleza"')  # Encuentra la clave "fortaleza"
        inicio_oportunidad = reporte_texto.find('"oportunidad"')  # Encuentra la clave "oportunidad"
        inicio_observaciones = reporte_texto.find('"perfil"')  # Encuentra la clave "observaciones"
        # Extraer el contenido entre las llaves
        fin_fortaleza = reporte_texto.find('",', inicio_fortaleza)  # Final del valor de "fortaleza"
        texto1 = reporte_texto[inicio_fortaleza:fin_fortaleza].strip()

        # Extraer el contenido de "oportunidad"
        fin_oportunidad = reporte_texto.find('\n', inicio_oportunidad + len('"oportunidad"'))
        texto2 = reporte_texto[inicio_oportunidad:fin_oportunidad].strip()
        
        # Extraer el contenido de "observaciones"
        fin_observaciones = reporte_texto.find('\n', inicio_observaciones + len('"perfil"'))
        texto3 = reporte_texto[inicio_observaciones:fin_observaciones].strip()
        
        print("ok-grupo 3")
        # Guardar el reporte en la base de datos
        Reporte.objects.create(
            nivel=grupo,
            referencia_id=usuario.id,  # O el ID de referencia correspondiente
            texto_fortalezas=texto1,
            texto_oportunidades=texto2,
            observaciones=texto3,
            fecha_generacion=now(),
            usuario_generador=usuario
        )
        print("ok-grupo 4")
        print("Reporte guardado exitosamente.")
    except Exception as e:
            print(f"Error al guardar el reporte: {e}")
    return {
            "status": "success",
            #"reporte": reporte_obj.id,
            #"datos_tutores": datos_tutores
        }

    