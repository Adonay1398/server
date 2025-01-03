import unicodedata
from collections import defaultdict

def normalizar_palabra(palabra):
    """
    Normaliza una palabra eliminando acentos y signos de puntuación.
    """
    return ''.join(
        c for c in unicodedata.normalize('NFD', palabra)
        if unicodedata.category(c) != 'Mn'
    ).lower().replace('.', '').replace(',', '')

def procesar_datos_promedios(datos_promedios):
    """
    Filtra los datos de promedios eliminando palabras similares y calculando sus promedios.
    
    Args:
        datos_promedios (dict): Diccionario con indicadores o constructos y sus scores.
        
    Returns:
        list: Lista de promedios únicos con palabras normalizadas.
    """
    # Diccionario para agrupar palabras normalizadas y sus valores
    agrupados = defaultdict(list)
    
    # Procesar los datos para normalizar y agrupar
    for item in datos_promedios:
        palabra_normalizada = normalizar_palabra(item['nombre'])
        agrupados[palabra_normalizada].append(item['prom_score'])
    
    # Calcular el promedio por palabra agrupada
    resultado = [
        {"nombre": palabra, "prom_score": sum(scores) // len(scores)}
        for palabra, scores in agrupados.items()
    ]
    
    return resultado
