import os
from typing import Literal
from langchain_community.chat_models import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate


model = ChatOpenAI(model="gpt-4")
parser = StrOutputParser()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

def prompt() -> ChatPromptTemplate:
    system_template = "Actúa como si fueras un analista de datos en una empresa de consultoría. Necesitan que analices los siguientes datos psicológicos y generes un informe con base a ellos."

    prompt_templates = """Genera {tipo_de_reporte} en base a los siguientes datos:

Nivel de análisis: {nivel_de_analisis}

Detalles específicos: {detalles_especificos}

Datos:
{datos}

Haz un análisis y proporciona {objetivo_informe}. La persona que va a leer el análisis es {lector}. Regresa la respuesta en formato JSON, con los datos que consideres necesarios: fortalezas y áreas de oportunidad. Utiliza formato markdown para dar formato a tu respuesta, como viñetas, subrayado, etc.

Ejemplo de respuesta:

  "fortalezas": Análisis sobre la fortaleza de los datos
  "oportunidad": Análisis sobre las áreas de oportunidad de los datos
"""

    prompt_template = ChatPromptTemplate.from_messages(
        [("system", system_template), ("user", prompt_templates)]
    )
    return prompt_template

from langchain_core.output_parsers import JsonOutputParser

parser = JsonOutputParser()  # Asegura que el resultado sea JSON

def make_analysis(data: dict, report: Literal['reporte', 'retroalimentación'], referencia: Literal['constructo', 'indicador']) -> dict:
    tipo_de_reporte = ['una retroalimentación hacia el tutor', 'un reporte']
    nivel_de_analisis = ['tutor', 'coordinador programa educativo', 'coordinador institución educativa', 'coordinador región', 'coordinador país']
    detalles_especificos = ['', 'los datos son la media, desviación estándar, moda']
    objetivos_informe = ['una retroalimentación', 'un reporte']

    promptTemplate = prompt()

    chain = promptTemplate | model | parser

    resultado = chain.invoke({
        "tipo_de_reporte": tipo_de_reporte[1],
        "lector": nivel_de_analisis[0],
        "nivel_de_analisis": nivel_de_analisis[0],
        "detalles_especificos": detalles_especificos[0],
        "objetivo_informe": objetivos_informe[1],
        "datos": data
    })

    print(f"Resultado de chain.invoke: {resultado}")  # Depuración
    return resultado
