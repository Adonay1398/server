import random
from faker import Faker
from django.contrib.auth.models import User
from api.models import Instituto, Departamento, Carrera, Profile, DatosAplicacion, ScoreConstructo, ScoreIndicador, Constructo, Indicador, Cuestionario, IndicadorConstructo

fake = Faker()

def clean_previous_data():
    # Eliminar datos anteriores
    ScoreConstructo.objects.all().delete()
    ScoreIndicador.objects.all().delete()
    DatosAplicacion.objects.all().delete()
    Profile.objects.all().delete()
    User.objects.filter(is_superuser=False).delete()  # Mantener superusuarios
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

    # Crear el departamento
    departamento, created = Departamento.objects.get_or_create(
        nombre="Sistemas Computacionales",
        defaults={"jefe": fake.name()}
    )

    # Crear la carrera
    carrera, created = Carrera.objects.get_or_create(
        nombre="Ingeniería en Sistemas Computacionales",
        defaults={"departamento": departamento, "instituto": instituto}
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

    # Crear cuestionarios si no existen
    cuestionarios_data = [
        {"nombre_corto": "Cuestionario 1", "nombre_largo": "Cuestionario de Prueba 1", "observaciones": "Observaciones 1"},
        {"nombre_corto": "Cuestionario 2", "nombre_largo": "Cuestionario de Prueba 2", "observaciones": "Observaciones 2"},
        {"nombre_corto": "Cuestionario 3", "nombre_largo": "Cuestionario de Prueba 3", "observaciones": "Observaciones 3"},
    ]

    for cuestionario_data in cuestionarios_data:
        Cuestionario.objects.get_or_create(
            nombre_corto=cuestionario_data["nombre_corto"],
            defaults={"nombre_largo": cuestionario_data["nombre_largo"], "observaciones": cuestionario_data["observaciones"]}
        )

    # Verificar la existencia de cuestionarios
    cuestionarios = Cuestionario.objects.all()
    if not cuestionarios.exists():
        print("No hay cuestionarios disponibles.")
        return

    # Crear una única aplicación
    datos_aplicacion = DatosAplicacion.objects.create(
        fecha=fake.date(),
        hora=fake.time(),
        observaciones=fake.text()
    )
    datos_aplicacion.cuestionario.set(cuestionarios)

    # Crear usuarios y sus perfiles
    for _ in range(10):
        user = User.objects.create_user(username=fake.user_name(), email=fake.email(), password="password123")
        profile = Profile.objects.create(user=user, nombre=fake.name(), correo_alternativo=fake.email(), carrera=carrera)

        # Crear score constructo
        for constructo in constructo_objects.values():
            ScoreConstructo.objects.create(
                aplicacion=datos_aplicacion,
                usuario=user,
                constructo=constructo,
                score=random.uniform(0, 100)
            )

        # Crear score indicador
        for indicador in Indicador.objects.all():
            ScoreIndicador.objects.create(
                aplicacion=datos_aplicacion,
                usuario=user,
                indicador=indicador,
                score=random.randint(0, 100)  # Corregido: random.randint(0, 100)
            )

# Ejecutar la función para crear datos falsos
create_fake_data()