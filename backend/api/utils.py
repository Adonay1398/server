



    

def calculate_construct_score(responses, reverse_items=None, weights=None, method="sum", normalize=False):
    """
    Calcula el score de un constructo en un MIQ.

    Args:
        responses (list): Lista de respuestas numéricas correspondientes a los ítems del constructo.
        reverse_items (list): Índices de los ítems que necesitan ser revertidos. (opcional)
                              Ejemplo: [0, 2] si los ítems en las posiciones 0 y 2 son negativos.
        weights (list): Pesos para cada ítem, si se requiere ponderación. (opcional)
                        Ejemplo: [0.5, 1, 0.8]
        method (str): Método para calcular el score ("sum", "average", "weighted"). 
                      - "sum": Suma de las respuestas.
                      - "average": Promedio de las respuestas.
                      - "weighted": Suma ponderada de las respuestas (requiere `weights`).
        normalize (bool): Si se debe normalizar el score en un rango de 0 a 1.

    Returns:
        float: Score calculado del constructo.
    """
    # Paso 1: Reversión de ítems
    if reverse_items:
        max_scale = max(responses)  # Asumimos que la escala es uniforme
        for index in reverse_items:
            responses[index] = (max_scale + 1) - responses[index]  # Reversión según fórmula: 6 - valor original

    # Paso 2: Calcular el score
    if method == "sum":
        score = sum(responses)
        max_score = len(responses) * max(responses)  # Puntaje máximo posible
        score = score / max_score
    elif method == "average":
        score = sum(responses) / len(responses)
    elif method == "weighted":
        if not weights or len(weights) != len(responses):
            raise ValueError("Se deben proporcionar pesos válidos para el cálculo ponderado.")
        score = sum(w * r for w, r in zip(weights, responses))
    else:
        raise ValueError("Método no válido. Usa 'sum', 'average' o 'weighted'.")



    return score*100 



""" 
def calcular_promedios_indicadores(scores):
    
    Calcula el promedio de los indicadores basado en los scores.
    
    indicadores = {}
    for score in scores:
        indicador = score.indicador.nombre
        if indicador not in indicadores:
            indicadores[indicador] = []
        indicadores[indicador].append(score.score)

    # Calcular promedios
    return {indicador: sum(valores) / len(valores) for indicador, valores in indicadores.items()}

def combinar_promedios(datos_nivel, grupos):
    
    Combina los promedios de los indicadores a nivel superior.
    
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
    Calcula los scores de los indicadores para cada tutor.
    
    tutores = CustomUser.objects.filter(groups__name="Tutor")
    resultados = {}

    for tutor in tutores:
        indicadores = ScoreIndicador.objects.filter(usuario=tutor).select_related('indicador')
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


def calcular_scores_jerarquicos(usuario, nivel, identificador):
    
    Calcula los scores de los indicadores jerárquicamente desde Carrera hasta Nación.
    
    resultados = {}

    if nivel == 'carrera':
        carrera = Carrera.objects.get(id=identificador) if identificador.isdigit() else Carrera.objects.get(nombre=identificador)
        indicadores = ScoreIndicador.objects.filter(usuario__carrera=carrera).select_related('indicador')
        promedios = calcular_promedios_indicadores(indicadores)
        for indicador, promedio in promedios.items():
            IndicadorPromedio.objects.update_or_create(
                nivel="carrera",
                grupo=Group.objects.get(name=f"Carrera - {carrera.nombre}"),
                indicador=indicador,
                defaults={'promedio': promedio}
            )
        resultados['carrera'] = {carrera.nombre: promedios}

    elif nivel == 'departamento':
        departamento = Departamento.objects.get(id=identificador) if identificador.isdigit() else Departamento.objects.get(nombre=identificador)
        carreras_departamento = Carrera.objects.filter(departamento=departamento)
        promedios_acumulados = {}
        for carrera in carreras_departamento:
            indicadores = ScoreIndicador.objects.filter(usuario__carrera=carrera).select_related('indicador')
            promedios = calcular_promedios_indicadores(indicadores)
            for indicador, promedio in promedios.items():
                if indicador not in promedios_acumulados:
                    promedios_acumulados[indicador] = []
                promedios_acumulados[indicador].append(promedio)
        for indicador in promedios_acumulados:
            promedios_acumulados[indicador] = sum(promedios_acumulados[indicador]) / len(promedios_acumulados[indicador])
            IndicadorPromedio.objects.update_or_create(
                nivel="departamento",
                grupo=Group.objects.get(name=f"Departamento - {departamento.nombre}"),
                indicador=indicador,
                defaults={'promedio': promedios_acumulados[indicador]}
            )
        resultados['departamento'] = {departamento.nombre: promedios_acumulados}

    # Repetir para otros niveles (Instituto, Región, Nación)...
    # Aquí puedes agregar el código para calcular los promedios para los niveles superiores

    return resultados

def calcular_scores_tutor():
    
    Calcula los scores de los indicadores para cada tutor.
    
    tutores = CustomUser.objects.filter(groups__name="Tutor")
    resultados = {}

    for tutor in tutores:
        indicadores = ScoreIndicador.objects.filter(usuario=tutor).select_related('indicador')
        promedios = calcular_promedios_indicadores(indicadores)

        for indicador, promedio in promedios.items():
            IndicadorPromedio.objects.update_or_create(
                nivel="tutor",
                grupo=None,
                indicador=indicador,
                defaults={'promedio': promedio}
            )
        resultados[tutor.username] = promedios

    
    return resultados """
    