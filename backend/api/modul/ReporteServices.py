def calculate_construct_score(responses, reverse_items=None):
    """
    Calcula el score normalizado de un constructo en MINI-IPIP (o similar).

    Args:
        responses (list): Lista de respuestas numéricas correspondientes a los ítems del constructo.
        reverse_items (list): Índices de los ítems que necesitan ser revertidos. (opcional).
                            Ejemplo: [0, 2] si los ítems en las posiciones 0 y 2 son negativos.

    Returns:
        float: Score normalizado del constructo.
    """
    # Paso 1: Reversión de ítems si es necesario
    if reverse_items:
        # max_scale = max(responses)  # Asumimos que la escala es uniforme
        max_scale = 5  # Asumimos que la escala es uniforme
        for index in reverse_items:
            responses[index] = (max_scale + 1) - responses[index]  # Reversión según fórmula

    # Paso 2: Calcular el score normalizado
    num_items = len(responses)  # Número de ítems en el constructo
    raw_score = sum(responses)  # Suma de las respuestas
    normalized_score = (raw_score - num_items) / (num_items * 4)  # Fórmula MATLAB

    return normalized_score * 100  # Retornar como porcentaje