import random
from faker import Faker
from api.models import CustomUser, Instituto, Departamento, Carrera, DatosAplicacion, ScoreConstructo, ScoreIndicador, Constructo, Indicador, Cuestionario, IndicadorConstructo, Pregunta, Respuesta

fake = Faker()

def clean_previous_data():
    # Eliminar datos anteriores
    ScoreConstructo.objects.all().delete()
    ScoreIndicador.objects.all().delete()
    DatosAplicacion.objects.all().delete()
    CustomUser.objects.filter(is_superuser=False).delete()  # Mantener superusuarios
    IndicadorConstructo.objects.all().delete()
    Indicador.objects.all().delete()
    Constructo.objects.all().delete()
    Carrera.objects.all().delete()
    Departamento.objects.all().delete()
    Instituto.objects.all().delete()
    Cuestionario.objects.all().delete()

def create_fake_data():
    # Limpiar datos anteriores
    clean_previous_data()

    # Crear el instituto
    instituto, created = Instituto.objects.get_or_create(
        nombre_completo="Instituto Tecnológico de Mérida",
        defaults={"tipo": "federal", "ruta": "merida"}
    )

    # Crear departamentos con diferentes planes de estudio
    departamento1, created = Departamento.objects.get_or_create(
        nombre="Sistemas Computacionales",
        defaults={"jefe": fake.name(), "plan_estudio": "Plan de Estudios 1"}
    )

    departamento2, created = Departamento.objects.get_or_create(
        nombre="Ingeniería Industrial",
        defaults={"jefe": fake.name(), "plan_estudio": "Plan de Estudios 2"}
    )

    # Crear carreras
    carrera1, created = Carrera.objects.get_or_create(
        nombre="Ingeniería en Sistemas Computacionales",
        defaults={"departamento": departamento1, "instituto": instituto}
    )

    
    # Crear constructos
    constructos = [
        "Madurez", "Responsabilidad", "Empatía", "Respeto", "Compasión", "Tolerancia",
        "Valoración", "Discreción", "Adaptabilidad", "Altruismo", "Humildad",
        "Habilidades interpersonales", "Manejo de grupo", "Orientación a la solución",
        "Compromiso", "Integridad", "Credibilidad", "Proactividad", "Planificación",
        "Aptitudes organizativas", "Flexibilidad", "Observación", "Resiliencia",
        "Autenticidad", "Optimismo", "Curiosidad", "Manejo de afectividad",
        "Mentalidad de crecimiento", "Interés", "Promover desarrollo autónomo",
        "Habilidades de pensamiento reflexivo", "Escrupulosidad", "Amabilidad", "Neuroticismo", "Extraversion",
        "Intelecto", "Imaginación", "Lógico-matemático", "Intrapersonal", "Lingüístico", "Espacial", "Musical", "Interpersonal", "Corporal-cinestésico"
    ]

    constructo_objects = {}
    for name in constructos:
        constructo, created = Constructo.objects.get_or_create(descripcion=name, defaults={'acronimo': name[:4].upper()})
        constructo_objects[name] = constructo

    # Crear indicadores y asociar constructos
    indicadores = {
        "Interacción social": [
            "Madurez", "Responsabilidad", "Empatía", "Respeto", "Compasión", "Tolerancia",
            "Valoración", "Discreción", "Adaptabilidad", "Altruismo", "Humildad",
            "Habilidades interpersonales", "Manejo de grupo"
        ],
        "Toma de decisiones": [
            "Orientación a la solución", "Compromiso", "Integridad", "Credibilidad",
            "Proactividad", "Planificación", "Aptitudes organizativas"
        ],
        "Autorregulación emocional y afectiva": [
            "Flexibilidad", "Observación", "Resiliencia", "Autenticidad", "Optimismo",
            "Curiosidad", "Manejo de afectividad", "Mentalidad de crecimiento"
        ],
        "Desarrollo personal y aprendizaje": [
            "Interés", "Promover desarrollo autónomo", "Habilidades de pensamiento reflexivo"
        ],
        "Inteligencia multiple": ["Lógico-matemático", "Intrapersonal", "Lingüístico", "Espacial", "Musical", "Interpersonal",
            "Corporal-cinestésico"],
        
        "Personalidad": [
            "Escrupulosidad", "Neuroticismo", "Extraversion", "Intelecto", "Imaginación"
        ]
    }

    for indicador_name, constructo_names in indicadores.items():
        indicador, created = Indicador.objects.get_or_create(nombre=indicador_name)
        for constructo_name in constructo_names:
            IndicadorConstructo.objects.get_or_create(indicador=indicador, constructo=constructo_objects[constructo_name])

# Ejecutar la función para crear datos falsos
create_fake_data()