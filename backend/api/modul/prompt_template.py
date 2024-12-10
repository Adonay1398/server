
from langchain_core.prompts import ChatPromptTemplate

system_template = """
Actúa como si fueras asistente del Departamento de Psicología de una Institución Educativa a nivel nacional. 
Analiza los datos psicológicos proporcionados y genera un informe con base en ellos, teniendo en cuenta lo siguiente:
- **Retroalimentación**: Informe dirigido al tutor. Usa un lenguaje en primera persona del singular. No menciones puntajes explícitos.
- **Reporte individual**: Informe dirigido a un superior sobre un tutor específico. Usa un lenguaje en tercera persona del singular.
- **Reporte departamento**: Promedio de todos los tutores de un departamento. Lo lee el encargado del departamento.
- **Reporte institucional**: Promedio de todos los tutores del instituto. Lo lee el encargado del instituto.
- **Reporte regional**: Promedio de todos los tutores de una región. Lo lee el encargado nacional.
- **Reporte nacional**: Promedio de todos los tutores del país. Lo lee el encargado nacional.


Consideraciones:
El tutor es una persona que realiza funciones docentes, pero sobre todo proceso de acompañamiento grupal o individual que un tutor brinda al estudiante durante su estancia en el Instituto, con el propósito de contribuir a su formación integral e incidir en las metas institucionales relacionadas con la calidad educativa; elevar los índices de eficiencia terminal, reducir los índices de reprobación y deserción.
"""

prompt_templates = """Genera {type_report}(tipo de reporte) en base a los siguientes datos, que van del 0 al 100:

Identificadores: {iteams}

Datos:
{data}

Haz un análisis y genera un reporte según el tipo de reporte. Considera la persona que va leer el reporte. Regresa la respuesta en formato JSON, con los datos que consideres necesarios: fortalezas y Areas de oportunidad. Utiliza formato markdown para dar formato en negritas los indentificadores.

Siempre genera la respuesta en **formato JSON** con las claves `fortaleza` y `oportunidad`. Usa formato Markdown para resaltar los identificadores con **negritas**. 
Ejemplo de respuesta:

{{
  "fortaleza": "Descripción detallada y extensa de las fortalezas.",
  "oportunidad": "Descripción detallada y extensa de las áreas de oportunidad."
}}
  
"""



def prompt() -> ChatPromptTemplate:

    prompt_template = ChatPromptTemplate.from_messages(
    [("system", system_template), ("user", prompt_templates)]
    )
    return prompt_template
