import random
from faker import Faker
from django.contrib.auth import get_user_model
from api.models import DatosAplicacion, Instituto, Departamento, Carrera, Cuestionario, Pregunta, Respuesta, ScoreConstructo, ScoreIndicador, Constructo, Indicador

fake = Faker()

def create_fake_users():
    User = get_user_model()

    # Obtener o crear el instituto
    instituto, created = Instituto.objects.get_or_create(
        nombre_completo="Instituto Tecnológico de Mérida",
        defaults={"tipo": "federal", "ruta": "merida"}
    )

    # Obtener o crear el departamento
    departamento, created = Departamento.objects.get_or_create(
        nombre="Sistemas Computacionales",
        defaults={"jefe": fake.name(), "plan_estudio": "Plan de Estudios 1"}
    )

    # Obtener o crear la carrera
    carrera, created = Carrera.objects.get_or_create(
        nombre="Ingeniería en Sistemas Computacionales",
        defaults={"departamento": departamento, "instituto": instituto}
    )

    # Obtener los cuestionarios
    cuestionarios = Cuestionario.objects.all()
    if cuestionarios.count() < 2:
        print("Se requieren al menos 2 cuestionarios en la base de datos.")
        return

    # Crear una única aplicación para todos los usuarios
    datos_aplicacion = DatosAplicacion.objects.create(
        fecha=fake.date(),
        hora=fake.time(),
        observaciones=fake.text()
    )
    datos_aplicacion.cuestionario.set(cuestionarios[:2])  # Asignar los primeros 2 cuestionarios

    # Crear 10 usuarios falsos
    for _ in range(10):
        user = User.objects.create_user(
            username=fake.user_name(),
            password='password',
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            email=fake.email(),
            fecha_nacimiento=fake.date_of_birth(),
            carrera=carrera
        )

        # Asignar respuestas a las preguntas de los cuestionarios
        for cuestionario in cuestionarios[:2]:  # Solo los primeros 2 cuestionarios
            for pregunta in Pregunta.objects.filter(cuestionario=cuestionario):
                Respuesta.objects.create(
                    pregunta=pregunta,
                    cve_aplic=datos_aplicacion,
                    user=user,
                    valor=str(random.randint(1, 5))
                )

        # Asignar scores a los constructos e indicadores
        for constructo in Constructo.objects.all():
            ScoreConstructo.objects.create(
                usuario=user,
                constructo=constructo,
                aplicacion=datos_aplicacion,  # Asignar la aplicación
                score=random.randint(0, 100)
            )

        for indicador in Indicador.objects.all():
            ScoreIndicador.objects.create(
                usuario=user,
                indicador=indicador,
                aplicacion=datos_aplicacion,  # Asignar la aplicación
                score=random.randint(0, 100)
            )

    print("Usuarios falsos creados exitosamente.")

# Ejecutar la función para crear usuarios falsos
create_fake_users()