import os
from typing import Literal
from langchain.chat_models import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from .prompt_template import prompt

# Configurar la clave de API de OpenAI
#os.environ["OPENAI_API_KEY"] = "tu_clave_de_api"

# Configurar el modelo de OpenAI
model = ChatOpenAI(
    model="gpt-4",
    temperature=0,
)

# Configurar el parser de salida
parser = StrOutputParser()

def make_analysis(
        data: dict,
        report: Literal['retroalimentación', 'individual', 'departamento', 'institucional', 'regional', 'nacional'],
        referencia: Literal['constructo', 'indicador']) -> str:

    if not isinstance(data, dict):
        raise TypeError("El parámetro 'data' debe ser un diccionario.")

    if report not in ['retroalimentación', 'individual', 'departamento', 'institucional', 'regional', 'nacional']:
        raise ValueError("El parámetro 'report' debe ser 'reporte' o 'retroalimentación'.")

    if referencia not in ['constructo', 'indicador']:
        raise ValueError("El parámetro 'referencia' debe ser 'constructo' o 'indicador'.")

    type_report = {
        'retroalimentación': 'retroalimentación',
        'individual': 'reporte individual',
        'departamento': 'reporte departamento',
        'institucional': 'reporte institucional',
        'regional': 'reporte regional',
        'nacional': 'reporte nacional'
    }
    data = {indicador["nombre"]: indicador["prom_score"] for indicador in data.get("indicador", [])}

    print(data)
    promptTemplate = prompt()

    chain = promptTemplate | model | parser
    return chain.invoke({
        'type_report': type_report[report],
        'iteams': data.keys(),
        'data': data
    })