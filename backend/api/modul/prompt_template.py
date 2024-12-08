from langchain_core.prompts import ChatPromptTemplate

system_template="Actua como si fueras un analista de datos en una empresa de consultoría. Necesitan que analices el sisguientes datos psicológicos y generes un informe con base a ellos."

prompt_templates = """Genera {tipo_de_reporte} en base a los siguientes datos:

Nivel de análisis: {nivel_de_analisis}

Detalles específicos: {detalles_especificos}

Datos:
{datos}

Haz un análisis y proporciona {objetivo_informe}. La persona que va a leer el análisis es {lector}. Regresa la respuesta en formato JSON, con los datos que consideres necesarios: fortalezas y Areas de oportunidad. Utiliza formato markdown para dar formato a tu respuesta, como viñetas, subrayado, etc.

Ejemplo de respuesta:

  "fortalezas": Analisis sobre la fortaleza de los datos
  "oportunidad": Analisis sobre las areas de oportunidad de los datos
"""



def prompt() -> ChatPromptTemplate:

    prompt_template = ChatPromptTemplate.from_messages(
    [("system", system_template), ("user", prompt_templates)]
    )
    return prompt_template