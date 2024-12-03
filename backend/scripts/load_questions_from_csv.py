import csv
import os
from api.models import Pregunta, Indicador, Constructo, Cuestionario

def load_questions_from_csv(csv_file):
    # Obtener la ruta absoluta del archivo CSV
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_path = os.path.join(base_dir, csv_file)

    try:
        with open(csv_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            header = next(reader)  # Leer la primera fila para ignorarla
            header = [h.lstrip('\ufeff') for h in header]  # Eliminar el BOM del encabezado
            print(f"Encabezado detectado: {header}")

            for row_number, row in enumerate(reader, start=2):  # Comienza en la línea 2 (tras el encabezado)
                try:
                    # Extraer datos basados en el orden de las columnas
                    question_id = row[0]  # Columna 0
                    question_text = row[1]  # Columna 1
                    category_name = row[2]  # Columna 2
                    subcategory_names = row[3].split(';')  # Columna 3
                    scorekey = [int(x) for x in row[4].split(',')]  # Columna 4
                    cuestionario_name = row[5]  # Columna 5

                    # Obtener o crear el cuestionario
                    cuestionario, created = Cuestionario.objects.get_or_create(nombre_corto=cuestionario_name)

                    # Obtener o crear el indicador
                    indicador, created = Indicador.objects.get_or_create(nombre=category_name)

                    # Obtener o crear los constructos y asociarlos al indicador
                    constructos = []
                    for subcategory_name in subcategory_names:
                        constructo, created = Constructo.objects.get_or_create(
                            descripcion=subcategory_name.strip(),
                            defaults={'acronimo': subcategory_name[:3].upper()}
                        )
                        # Verificar que el objeto tenga un ID válido
                        if not constructo.cve_const:
                            constructo.save()
    
                        print(f"Constructo creado o recuperado: {constructo.descripcion}, ID: {constructo.cve_const}")
    
                        indicador.constructos.add(constructo)
                        constructos.append(constructo)

                    # Crear la pregunta y asignar los constructos a los campos cve_const1_id, cve_const2_id, etc.
                    pregunta_data = {
                        'texto_pregunta': question_text,
                        'scorekey': scorekey,
                        'cuestionario': cuestionario
                    }
                    for i, constructo in enumerate(constructos):
                        pregunta_data[f'cve_const{i+1}_id'] = constructo.cve_const  # Asignar el ID del constructo

                    pregunta, created = Pregunta.objects.update_or_create(
                        cve_pregunta=question_id,
                        defaults=pregunta_data
                    )

                    print(f'Successfully loaded question {question_id}')
                except KeyError as e:
                    print(f"Missing column in CSV: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

# Ejecutar la función con la ruta relativa al archivo CSV
load_questions_from_csv('MINI-IPIP.csv')