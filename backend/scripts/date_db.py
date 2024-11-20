from api.models import Indicador, Constructo, IndicadorConstructo

def clean_duplicates():
    descriptions = Constructo.objects.values_list('descripcion', flat=True)
    description_counts = {}
    
    for desc in descriptions:
        if desc in description_counts:
            description_counts[desc] += 1
        else:
            description_counts[desc] = 1

    duplicates = [desc for desc, count in description_counts.items() if count > 1]

    for desc in duplicates:
        constructos = Constructo.objects.filter(descripcion=desc)
        primary_constructo = constructos.first()  # Mantener el primer objeto
        for duplicate in constructos[1:]:
            # Aquí puedes manejar la consolidación de datos si es necesario
            duplicate.delete()

def create_test_data():
    # Limpiar duplicados antes de crear datos de prueba
    clean_duplicates()

    # Crear constructos si no existen
    constructos = [
        "Madurez", "Responsabilidad", "Empatía", "Respeto", "Compasión", "Tolerancia",
        "Valoración", "Discreción", "Adaptabilidad", "Altruismo", "Humildad",
        "Habilidades interpersonales", "Manejo de grupo", "Orientación a la solución",
        "Compromiso", "Integridad", "Credibilidad", "Proactividad", "Planificación",
        "Aptitudes organizativas", "Flexibilidad", "Observación", "Resiliencia",
        "Autenticidad", "Optimismo", "Curiosidad", "Manejo de afectividad",
        "Mentalidad de crecimiento", "Interés", "Promover desarrollo autónomo",
        "Habilidades de pensamiento reflexivo"
    ]

    constructo_objects = {}
    for name in constructos:
        constructo, created = Constructo.objects.get_or_create(descripcion=name, defaults={'signo': '+', 'acronimo': name[:3].upper()})
        constructo_objects[name] = constructo

    # Crear indicadores y asociar constructos
    indicadores = {
        "Competencias de interacción social": [
            "Madurez", "Responsabilidad", "Empatía", "Respeto", "Compasión", "Tolerancia",
            "Valoración", "Discreción", "Adaptabilidad", "Altruismo", "Humildad",
            "Habilidades interpersonales", "Manejo de grupo"
        ],
        "Competencias de toma de decisiones": [
            "Orientación a la solución", "Compromiso", "Integridad", "Credibilidad",
            "Proactividad", "Planificación", "Aptitudes organizativas"
        ],
        "Competencias de autorregulación emocional y afectiva": [
            "Flexibilidad", "Observación", "Resiliencia", "Autenticidad", "Optimismo",
            "Curiosidad", "Manejo de afectividad", "Mentalidad de crecimiento"
        ],
        "Competencias de desarrollo personal y aprendizaje": [
            "Interés", "Promover desarrollo autónomo", "Habilidades de pensamiento reflexivo"
        ]
    }

    for indicador_name, constructo_names in indicadores.items():
        indicador, created = Indicador.objects.get_or_create(nombre=indicador_name)
        for constructo_name in constructo_names:
            IndicadorConstructo.objects.get_or_create(indicador=indicador, constructo=constructo_objects[constructo_name])

    instituto = [
        {"nombre_completo:": "Instituto Tecnológico de Mérida" },
    ]
# Ejecutar la función para crear datos de prueba
create_test_data()