import os
from typing import Literal
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
import openai
from .prompt_template import prompt
import json
import time

# Inicializar modelo de OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")




model = ChatOpenAI(
    model="gpt-4",
    temperature=0,
)





parser = StrOutputParser()


def make_analysis(
        data:dict, 
        report:Literal['retroalimentación','individual','departamento','institucional','regional','nacional'],referencia:Literal['constructo','indicador']) -> dict:
    
    if not isinstance(data, dict):
        raise TypeError("El parámetro 'data' debe ser un diccionario.")
    
    if report not in ['retroalimentación','individual','departamento','institucional','regional','nacional']:
        raise ValueError("El parámetro 'report' debe ser 'reporte' o 'retroalimentación'.")
    
    if referencia not in ['constructo', 'indicador']:
        raise ValueError("El parámetro 'referencia' debe ser 'constructo' o 'indicador'.")

    type_report={
        'retroalimentación':'retroalimentación',
        'individual': 'reporte individual',
        'departamento':'reporte departamento',
        'institucional':'reporte institucional',
        'regional':'reporte regional',
        'nacional':'reporte nacional'
    }
    #print(data)
    data = {indicador["nombre"]: indicador["prom_score"] for indicador in data.get("indicador", [])}
    #n = 1 if report == 'retroalimentación' else 2
    n=2 
    response_dict = {}
    for i in range(n):    
        promptTemplate = prompt(i)

        # Iniciar cronómetro
        start_time = time.time()

        chain = promptTemplate | model | parser
        response = chain.invoke({
            'type_report': type_report[report],
            'iteams':data.keys(),
            'data': data
        })
        # Detener cronómetro
        end_time = time.time()
        elapsed_time = end_time - start_time
        print (response)
        # Mostrar tiempo de respuesta
        print(f"Tiempo de respuesta: {elapsed_time:.2f} segundos")
        
        response_dict.update(json.loads(response))


    return response_dict 