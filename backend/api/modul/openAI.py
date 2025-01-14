import os
from typing import Literal
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
import openai
from .prompt_template import prompt
import json
import time
load_dotenv()
# Inicializar modelo de OpenAI

os.getenv("OPENAI_API_KEY")




model = ChatOpenAI(
    model="gpt-4",
    temperature=0,
)





parser = StrOutputParser()

import re
import json
import time

def limpiar_response(response):
    """
    Elimina caracteres de control del 'response'.
    """
    return re.sub(r'[\x00-\x1f\x7f]', '', response)

def make_analysis(
        data: dict, 
        report: Literal['retroalimentación', 'individual', 'carrera','departamento', 'institucional', 'regional', 'nacional'],
        referencia: Literal['constructo', 'indicador']
    ) -> dict:
    
    if not isinstance(data, dict):
        raise TypeError("El parámetro 'data' debe ser un diccionario.")
    
    if report not in ['retroalimentación', 'individual', 'carrera','departamento', 'institucional', 'regional', 'nacional']:
        raise ValueError("El parámetro 'report' es inválido.")
    
    if referencia not in ['constructo', 'indicador']:
        raise ValueError("El parámetro 'referencia' debe ser 'constructo' o 'indicador'.")

    type_report = {
        'retroalimentación': 'retroalimentación',
        'individual': 'reporte individual',
        'carrera': 'reporte plan de estudios',
        'departamento': 'reporte departamento',
        'institucional': 'reporte institucional',
        'regional': 'reporte regional',
        'nacional': 'reporte nacional'
    }
    
    n = 1 if report == 'retroalimentación' else 2
    response_dict = {}

    for i in range(n):    
        promptTemplate = prompt(i)
        start_time = time.time()

        try:
            chain = promptTemplate | model | parser
            response = chain.invoke({
                'type_report': type_report[report],
                'iteams': data.keys(),
                'data': data
            })

            response = limpiar_response(response)  # Limpia el response antes de procesarlo
            response_dict.update(json.loads(response))
        
        except json.JSONDecodeError as e:
            print(f"Error al decodificar JSON: {e}")
            print(f"Contenido problemático: {repr(response)}")
            raise ValueError("Error al procesar el response en JSON.")
        except Exception as e:
            print(f"Error inesperado: {e}")
            raise

        elapsed_time = time.time() - start_time
        print(f"Tiempo de respuesta: {elapsed_time:.2f} segundos")
    
    return response_dict