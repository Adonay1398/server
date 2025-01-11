import json
from django.contrib.auth.models import Group
from api.models import  AsignacionCuestionario, Constructo, Cuestionario, CustomUser, DatosAplicacion, Departamento, Indicador, IndicadorPromedio, Region, Instituto, Carrera, Reporte, ScoreIndicador, ScoreConstructo
from api.modul.openAI import make_analysis
from django.utils.timezone import now
from collections import defaultdict
from django.db import transaction
import logging
logger = logging.getLogger(__name__)

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
            
        
        elif grupo.name == "Tutores":
            tutores = CustomUser.objects.filter(user=usuario)  # Solo el tutor actual
        else:
            raise ValueError("El grupo del usuario no está definido para esta operación.")
        
        
        

        return tutores

    except Exception as e:
        raise ValueError(f"Error al obtener tutores: {str(e)}")
    
    
    
    


def calcular_scores_tutores(tutores, aplicacion, cuestionario, usuario):
    """
    Calcula, normaliza y guarda los promedios generales de constructos e indicadores para los tutores.
    Devuelve promedios por constructo e indicador, agrupados según la relación entre ellos.
    """
    indicadores_totales = defaultdict(list)
    constructos_totales = defaultdict(list)
    constructo_indicador_relaciones = defaultdict(lambda: defaultdict(list))

    try:
        with transaction.atomic():  # Asegurar la consistencia en los datos
            for tutor in tutores:
                # Obtener scores de constructos e indicadores
                scores_constructos = ScoreConstructo.objects.filter(
                    usuario=tutor,
                    aplicacion=aplicacion
                ).distinct()

                scores_indicadores = ScoreIndicador.objects.filter(
                    usuario=tutor,
                    aplicacion=aplicacion
                ).distinct()

                # Acumular scores por indicador y constructo
                for score in scores_indicadores:
                    indicadores_totales[score.indicador.nombre].append(score.score)

                for score in scores_constructos:
                    if not isinstance(score.constructo, Constructo):
                        raise ValueError(f"'{score.constructo}' no es una instancia válida de Constructo.")

                    constructos_totales[score.constructo.descripcion].append(score.score)

                    for indicador in score.constructo.indicadores_set.all():
                        # Acumular scores para constructos bajo el indicador
                        constructo_indicador_relaciones[indicador.nombre][score.constructo.descripcion].append(score.score)

            # Calcular promedios generales por constructo
            promedios_constructos = [
                {
                    "nombre": constructo,
                    "prom_score": int(sum(scores) / len(scores))
                }
                for constructo, scores in constructos_totales.items()
            ]

            # Calcular promedios generales por indicador
            promedios_indicadores = [
                {
                    "nombre": indicador ,
                        "prom_score": int(
                        sum(score for constructo_scores in constructos.values() for score in constructo_scores) / 
                        sum(len(constructo_scores) for constructo_scores in constructos.values())
                    ),
                        "constructos": [
                            {
                                "nombre": constructo,
                                "prom_score": int(sum(constructo_scores) / len(constructo_scores))
                            }
                            for constructo, constructo_scores in constructos.items()
                        ]
                }
                for indicador, constructos in constructo_indicador_relaciones.items()
                    
                    
            ]

            print("ok-tutores 2")

    except Exception as e:
        print(f"Error al calcular y guardar los promedios: {e}")
        raise

    return {
        #"promedios_constructos": promedios_constructos,
        "promedios_indicadores": promedios_indicadores
    }

def generar_reporte_individual_por_tutor( usuario,aplicacion,cuestionario_id):
    """
    Genera reportes individuales para cada tutor relacionado con la aplicación.

    Args:
        tutores (QuerySet): Lista de tutores relacionados.
        usuario (CustomUser): Usuario autenticado.
        aplicacion (DatosAplicacion): Aplicación actual.
        cuestionario_id (int): ID del cuestionario asociado.

    Returns:
        dict: Resultado del proceso de generación.
    """
    resultados = {"success": 0, "errors": 0, "details": []}

    grupo = usuario.groups.first().name

    
    try:
        # Calcular los scores del tutor
            scores_constructos = ScoreConstructo.objects.filter(usuario=usuario, aplicacion=aplicacion.cve_aplic).distinct()
            scores_indicadores = ScoreIndicador.objects.filter(usuario=usuario, aplicacion=aplicacion.cve_aplic).distinct()
            print("ok-tutores-indiv 0")
            # Preparar datos para make_analysis
            data = {
                indicador_score.indicador.nombre: {
                    "prom_score": indicador_score.score,
                    "constructos": [
                        {
                            "nombre": constructo_score.constructo.descripcion,
                            "prom_score": constructo_score.score
                        }
                        for constructo_score in scores_constructos
                        if indicador_score.indicador in constructo_score.constructo.indicadores_set.all()
                    ]
                }
                for indicador_score in scores_indicadores
            }
            nombres_filtrar ={"Autorregulación emocional y afectiva","Interacción social","Toma de decisiones",}
            data_filtrada = {
                indicador_score.indicador.nombre:{
                    "prom_score":indicador_score.score,
                    "constructos":[
                        {
                            "nombre":constructo_score.constructo.descripcion,
                            "prom_score":constructo_score.score
                            
                        }
                        for constructo_score in scores_constructos
                        if indicador_score.indicador in constructo_score.constructo.indicadores_set.all()
                    ]
                }
                for indicador_score in scores_indicadores 
                if indicador_score.indicador.nombre in nombres_filtrar
                }
            print(data_filtrada)
            print("ok-tutores-indiv 1")
            # Generar el reporte con make_analysis
            reporte = make_analysis(data=data_filtrada, report="individual", referencia='indicador')
            print(reporte)
            # Extraer texto del análisis
            texto1 = reporte.get("fortaleza", "").strip()
            texto2 = reporte.get("oportunidad", "").strip()
            texto3 = reporte.get("perfil", "").strip()
            print("ok-tutores-indiv 3")
            # Guardar solo hasta el nivel del usuario
            
            print("ok-tutores-indiv 4")
            # Crear el reporte en la base de datos
            Reporte.objects.create(
                nivel="Tutores",
                referencia_id=aplicacion.cve_aplic,
                texto_fortalezas=texto1,
                texto_oportunidades=texto2,
                observaciones=texto3,
                fecha_generacion=now(),
                usuario_generador=usuario,
                carrera=usuario.carrera if hasattr(usuario, 'carrera') and usuario.carrera else None,
                departamento=usuario.departamento if hasattr(usuario, 'departamento') and usuario.departamento else None,
                institucion=usuario.instituto if hasattr(usuario, 'instituto') and usuario.instituto else None,
                region=usuario.region if hasattr(usuario, 'region') and usuario.region else None,
                datos_promedios=data
            )
            print("ok-tutores-indiv 5")
            return {
            "status": "success",
            "message": "Reporte generado correctamente."
        }
    except Exception as e:
        logger.error(f"Error al generar el reporte: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

def generar_reporte_por_grupo(usuario, aplicacion,cuestionario_id):
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
        print("ok-datos promedios 1")
        print(datos_tutores)
        #data = {entry["nombre"]: entry["prom_score"] for entry in datos_tutores["promedios_indicadores"]}
        data = {
            indicador["nombre"]: {
                "prom_score": indicador["prom_score"],
                "constructos": [
                    {"nombre": constructo["nombre"], "prom_score": constructo["prom_score"]}
                    for constructo in indicador["constructos"]
                ]
            }
            for indicador in datos_tutores["promedios_indicadores"]
        }
        print("datoa ok")
        try:
            nombres_filtrar ={"Autorregulación emocional y afectiva","Interacción social","Toma de decisiones",}
            print(nombres_filtrar)
            data_filtrada ={
                indicador["nombre"]:{
                    "prom_score":indicador["prom_score"],
                    "constructos":[
                        {"nombre":constructo["nombre"],"prom_score":constructo["prom_score"]}
                        for constructo in indicador["constructos"]
                    ]
                }
                for indicador in datos_tutores["promedios_indicadores"]
                if indicador["nombre"] in nombres_filtrar
            }
        except KeyError as e:
            print(f"Error al filtrar los datos: {e}")
            #print("datos:"{datos_tutores})
            raise
        
        print("Prepared data for analysis:", data_filtrada)
        #datos_promedios1 = procesar_datos_promedios(data)

        print("ok-grupo data ok")
        # Determinar el tipo de reporte según el grupo
        grupo = usuario.groups.first().name
        report = {
            "Coordinador de Tutorias por Departamento": "departamento",
            "Coordinador de Tutorias por Institucion": "institucional",
            "Coordinador de Tutorias a Nivel Regional": "regional",
            "Coordinador de Tutorias a Nivel Nacional": "nacional",
            "Tutores": "individual"
        }.get(grupo, "departamento")
        print("Report type:", report)
        print("ok-grupo 0")
        # Generar el reporte con make_analysis
        
        reporte = make_analysis(data=data_filtrada, report=report, referencia='indicador')
        
        print("Reporte generado:")
        #print(dict(reporte))
        print("ok-grupo 2")
        # Convertir el reporte a texto y extraer información relevante
        #reporte_texto = json.dumps(reporte, ensure_ascii=False, indent=4)
        texto1 = reporte.get("fortaleza", "").strip()
        texto2 = reporte.get("oportunidad", "").strip()
        texto3 = reporte.get("perfil", "").strip()
        print("ok-grupo 3")
        
        """ carrera = usuario.carrera if grupo == "Coordinador de Plan de Estudios" else None
        departamento = carrera.departamento if grupo in ["Coordinador de Tutorias por Departamento"] else None
        institucion = departamento.instituto if grupo in ["Coordinador de Tutorias por Institucion", "Coordinador de Tutorias por Departamento", "Coordinador de Plan de Estudios"] else None
        region = institucion.region if grupo in ["Coordinador de Tutorias a Nivel Regional", "Coordinador de Tutorias por Institucion", "Coordinador de Tutorias por Departamento", "Coordinador de Plan de Estudios"] else None

        """
        # Guardar el reporte en la base de datos
        Reporte.objects.create(
            nivel=grupo,
            referencia_id=aplicacion.cve_aplic,  # O el ID de referencia correspondiente
            texto_fortalezas=texto1,
            texto_oportunidades=texto2,
            observaciones=texto3,
            fecha_generacion=now(),
            usuario_generador=usuario,
            carrera=usuario.carrera if hasattr(usuario, 'carrera') and usuario.carrera else None,
            departamento=usuario.departamento if hasattr(usuario, 'departamento') and usuario.departamento else None,
            institucion=usuario.instituto if hasattr(usuario, 'instituto') and usuario.instituto else None,
            region=usuario.region if hasattr(usuario, 'region') and usuario.region else None,
            datos_promedios=data
        )

        print("ok-grupo 4")
        print("Reporte guardado exitosamente.")
        return {
            "status": "success",
            "message": "Reporte generado correctamente."
        }
    except Exception as e:
        logger.error(f"Error al generar el reporte: {e}")
        return {
            "status": "error",
            "message": str(e)
        }



def generar_reportes_aplicacion(aplicacion_id):
    """
    Genera reportes para todos los usuarios asignados a los cuestionarios de una aplicación,
    obteniendo scores de constructos e indicadores directamente de la base de datos.

    Args:
        aplicacion_id (int): ID de la aplicación cuyos reportes se generarán.

    Returns:
        dict: Resultado del proceso, incluyendo estadísticas de éxito y error.
    """
    try:
        # Obtener la aplicación
        aplicacion = DatosAplicacion.objects.get(cve_aplic=aplicacion_id)

        # Obtener todas las asignaciones completadas para esta aplicación
        asignaciones = AsignacionCuestionario.objects.filter(
            aplicacion=aplicacion,
            completado=True
        )

        if not asignaciones.exists():
            return {
                "status": "warning",
                "message": f"No hay asignaciones completadas para la aplicación {aplicacion.cve_aplic}."
            }

        resultados = {"success": 0, "errors": 0, "details": []}

        # Procesar cada asignación
        for asignacion in asignaciones:
            usuario = asignacion.usuario
            cuestionario = asignacion.cuestionario

            try:
                # Obtener scores de constructos e indicadores para el usuario
                scores_constructos = ScoreConstructo.objects.filter(
                    usuario=usuario,
                    aplicacion=aplicacion
                ).distinct()

                scores_indicadores = ScoreIndicador.objects.filter(
                    usuario=usuario,
                    aplicacion=aplicacion
                ).distinct()

                # Preparar las relaciones constructo-indicador
                data = {}
                for indicador_score in scores_indicadores:
                    indicador_nombre = indicador_score.indicador.nombre
                    if indicador_nombre not in data:
                        data[indicador_nombre] = {
                            "prom_score": indicador_score.score,
                            "constructs": []
                        }

                for constructo_score in scores_constructos:
                    constructo_nombre = constructo_score.constructo.descripcion
                    for indicador in constructo_score.constructo.indicadores_set.all():
                        if indicador.nombre in data:
                            data[indicador.nombre]["constructs"].append({
                                "nombre": constructo_nombre,
                                "prom_score": constructo_score.score
                            })

                # Generar reporte con make_analysis
                reporte = make_analysis(data=data, report="individual", referencia="indicador")

                # Extraer resultados del análisis
                texto1 = reporte.get("fortaleza", "").strip()
                texto2 = reporte.get("oportunidad", "").strip()
                texto3 = reporte.get("perfil", "").strip()

                # Identificar relaciones jerárquicas
                carrera = usuario.carrera
                departamento = carrera.departamento
                institucion = departamento.instituto
                region = institucion.region

                # Crear el reporte en la base de datos
                Reporte.objects.create(
                    nivel="individual",
                    referencia_id=aplicacion.cve_aplic,
                    texto_fortalezas=texto1,
                    texto_oportunidades=texto2,
                    observaciones=texto3,
                    fecha_generacion=now(),
                    usuario_generador=usuario,
                    carrera=carrera,
                    departamento=departamento,
                    institucion=institucion,
                    region=region,
                    datos_promedios=data
                )

                resultados["success"] += 1
            except Exception as e:
                resultados["errors"] += 1
                resultados["details"].append({
                    "usuario": usuario.email,
                    "error": str(e)
                })

        return {
            "status": "completed",
            "message": f"Proceso finalizado para la aplicación {aplicacion.cve_aplic}.",
            "results": resultados
        }

    except DatosAplicacion.DoesNotExist:
        return {
            "status": "error",
            "message": f"La aplicación con ID {aplicacion_id} no existe."
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error inesperado: {str(e)}"
        }
