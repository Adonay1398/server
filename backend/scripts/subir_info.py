import random
import csv
import os
import unicodedata
from faker import Faker
from django.contrib.auth import get_user_model
from django.utils import timezone
from api.models import (
    DatosAplicacion, Instituto, Departamento, Carrera, Cuestionario,
    Pregunta, Respuesta, Constructo, Indicador, IndicadorConstructo, CustomUser
)
from django.db.utils import IntegrityError

fake = Faker()

# Función para limpiar datos previos
def clean_previous_data():
    print("Limpiando datos anteriores...")
    IndicadorConstructo.objects.all().delete()
    Indicador.objects.all().delete()
    Constructo.objects.all().delete()
    Pregunta.objects.all().delete()
    CustomUser.objects.filter(is_superuser=False).delete()  # Mantener superusuarios
    DatosAplicacion.objects.all().delete()
    print("Datos limpiados.")

# Función para crear constructos
def create_constructs():
    print("Creando constructos...")
    construct_names = [
        "Madurez", "Responsabilidad", "Empatía", "Respeto", "Compasión", "Tolerancia",
        "Valoración", "Discreción", "Adaptabilidad", "Altruismo", "Humildad",
        "Habilidades interpersonales", "Manejo de grupo", "Orientación a la solución",
        "Compromiso", "Integridad", "Credibilidad", "Proactividad", "Planificación",
        "Aptitudes organizativas", "Flexibilidad", "Observación", "Resiliencia",
        "Autenticidad", "Optimismo", "Curiosidad", "Manejo de afectividad", "Mentalidad de crecimiento",
        "Interés", "Promover desarrollo autónomo", "Habilidades de pensamiento reflexivo",
        "Lógico-matemático", "Intrapersonal", "Lingüístico", "Espacial", "Musical", "Interpersonal",
        "Corporal-cinestésico", "Escrupulosidad", "Neuroticismo", "Extroversión", "Intelecto", "Imaginación"
    ]

    for construct_name in construct_names:
        Constructo.objects.get_or_create(
            descripcion=construct_name.strip(),
            defaults={'acronimo': construct_name[:3].upper()}
        )
    print("Constructos creados exitosamente.")

# Función para crear indicadores y relacionarlos con constructos
def create_indicators_and_relations():
    print("Creando indicadores y relaciones con constructos...")
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
        "Inteligencias múltiples": [
            "Lógico-matemático", "Intrapersonal", "Lingüístico", "Espacial", "Musical", "Interpersonal",
            "Corporal-cinestésico"
        ],
        "Personalidad": [
            "Escrupulosidad", "Neuroticismo", "Extroversión", "Intelecto", "Imaginación"
        ]
    }

    for indicador_name, construct_names in indicadores.items():
        indicador, _ = Indicador.objects.get_or_create(nombre=indicador_name)
        for construct_name in construct_names:
            try:
                constructo = Constructo.objects.get(descripcion=construct_name.strip())
                IndicadorConstructo.objects.get_or_create(indicador=indicador, constructo=constructo)
            except Constructo.DoesNotExist:
                print(f"Error: Constructo con descripcion '{construct_name}' no existe.")
    print("Indicadores y relaciones creados exitosamente.")

# Función para normalizar texto
def normalize_text(text):
    return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')

# Función para cargar preguntas desde un archivo CSV
def load_questions_from_csv(csv_file, encoding='utf-8'):
    print(f"Cargando preguntas desde {csv_file}...")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_dir, csv_file)

    with open(csv_path, newline='', encoding=encoding) as csvfile:
        reader = csv.reader(csvfile)
        header = next(reader)  # Ignorar encabezado
        for row in reader:
            question_id, question_text, category_name, subcategories, scorekey, cuestionario_name = row[:6]
            question_text = normalize_text(question_text)
            cuestionario, _ = Cuestionario.objects.get_or_create(nombre_corto=cuestionario_name)
            indicador, _ = Indicador.objects.get_or_create(nombre=category_name)

            for subcategory in subcategories.split(';'):
                # Crear constructo si no existe
                constructo, created = Constructo.objects.get_or_create(
                    descripcion=normalize_text(subcategory.strip()),
                    defaults={'acronimo': normalize_text(subcategory[:3].upper())}
                )
                IndicadorConstructo.objects.get_or_create(indicador=indicador, constructo=constructo)

                # Asociar pregunta al constructo y al cuestionario
                try:
                    Pregunta.objects.update_or_create(
                        cve_pregunta=question_id,
                        defaults={
                            'texto_pregunta': question_text,
                            'scorekey': list(map(int, scorekey.split(','))),
                            'cuestionario': cuestionario,
                            'cve_const1_id': constructo.pk  # Asignar constructo principal
                        }
                    )
                except IntegrityError:
                    print(f"Error: Pregunta con cve_pregunta {question_id} ya existe.")
    print("Preguntas cargadas exitosamente.")


# Script principal
def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
    import django
    django.setup()

    clean_previous_data()
    create_constructs()
    create_indicators_and_relations()
    load_questions_from_csv('MINI-IPIP.csv')  # Reemplaza con tu archivo CSV y especifica la codificación correcta
    print("Script ejecutado exitosamente.")

if __name__ == "__main__":
    main()