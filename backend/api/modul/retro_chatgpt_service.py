from api.models import RetroChatGPT, ScoreIndicador, ScoreConstructo
from .openAI import make_analysis  # Módulo para interactuar con la IA
from api.serializers import CuestionarioStatusSerializer


def validar_cuestionarios_completados(usuario, request):
    """
    Verifica si todos los cuestionarios asignados al usuario están completados
    reutilizando CuestionarioStatusSerializer.
    """
    # Validar que se reciba el request correctamente
    if not request:
        raise ValueError("El parámetro 'request' es obligatorio.")

    # Crear una instancia del serializador con el contexto adecuado
    serializer = CuestionarioStatusSerializer(context={'request': request})

    # Obtener cuestionarios pendientes ("on_hold")
    try:
        on_hold = serializer.get_on_hold(None)
    except Exception as e:
        print(f"Error al obtener cuestionarios pendientes: {e}")
        return False, ["Error al validar cuestionarios pendientes."]

    # Verificar si hay cuestionarios pendientes
    if on_hold['current'] or on_hold['past']:
        pendientes = [c['nombre'] for c in on_hold['current']] + [c['nombre'] for c in on_hold['past']]
        return False, pendientes

    return True, []



def calcular_scores(usuario):
    """
    Calcula los scores de constructos e indicadores para un usuario.
    """
    # Obtener los scores relacionados con el usuario
    scores = ScoreIndicador.objects.filter(usuario=usuario)

    # Diccionarios para almacenar resultados
    constructos = {}
    indicadores = {}

    for score in scores:
        # Procesar indicadores
        indicador_key = score.indicador.nombre  # Usar el nombre o ID del indicador
        if indicador_key not in indicadores:
            indicadores[indicador_key] = []
        indicadores[indicador_key].append(score.score)

        # Procesar constructos relacionados al indicador
        for constructo in score.indicador.constructos.all():
            constructo_key = constructo.descripcion  # Usar nombre o ID del constructo
            if constructo_key not in constructos:
                constructos[constructo_key] = []
            constructos[constructo_key].append(score.score)

    # Calcular promedios
    resultados_constructos = {k: sum(v) / len(v) for k, v in constructos.items()}
    resultados_indicadores = {k: sum(v) / len(v) for k, v in indicadores.items()}

    return resultados_constructos, resultados_indicadores


def generar_retro_chatgpt(usuario, cuestionario, datos_indicadores):
    """
    Genera la retroalimentación utilizando el módulo de análisis de IA.
    """
    # Llamada a la función make_analysis
    resultado = make_analysis(
        data=datos_indicadores,
        report='retroalimentación',
        referencia='constructo'
    )

    print(f"Resultado de make_analysis: {resultado}")  # Inspecciona el resultado

    # Verifica que el resultado sea un diccionario
    if not isinstance(resultado, dict):
        raise ValueError("El resultado de make_analysis no es un diccionario.")

    # Extraer fortalezas y oportunidades del resultado
    fortalezas = resultado.get("fortalezas", "No se identificaron fortalezas.")
    oportunidades = resultado.get("oportunidades", "No se identificaron áreas de oportunidad.")

    # Crear una instancia en la base de datos con el resultado
    retro = RetroChatGPT.objects.create(
        usuario=usuario,
        texto1=fortalezas,
        texto2=oportunidades,
        pdf_file=None  # Puedes agregar lógica para generar un PDF aquí
    )

    return retro



def procesar_cuestionarios(usuario, request):
    """
    Procesa los cuestionarios asociados al usuario y valida si están completos.
    """
    # Validar si todos los cuestionarios están completados
    completados, faltantes = validar_cuestionarios_completados(usuario, request)

    if not completados:
        return {"error": "Faltan cuestionarios por completar.", "pendientes": faltantes}

    # Si están completos, genera resultados (indicadores y retroalimentación)
    resultados_constructos, resultados_indicadores = calcular_scores(usuario)

    # Genera retroalimentación con el módulo de IA
    retro_chatgpt = generar_retro_chatgpt(usuario, cuestionario=None, datos_indicadores=resultados_indicadores)

    return {
        "indicadores": resultados_indicadores,
        "constructos": resultados_constructos,
        "retroalimentacion": {
            "text1": retro_chatgpt.texto1,
            "text2": retro_chatgpt.texto2,
        }
    }
