from django.core.management.base import BaseCommand
from api.models import Cuestionario, Pregunta, Indicador, Constructo, IndicadorConstructo
import pandas as pd
import os


class Command(BaseCommand):
    help = 'Uploads questionnaire data, creates constructs and indicators, links them, and splits constructs with "/".'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the CSV file containing questionnaire data.')

    def handle(self, *args, **kwargs):
        file_path = kwargs['file_path']

        # Ensure file exists
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"File not found: {file_path}"))
            return

        # Load the CSV file
        try:
            data = pd.read_csv(file_path)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error reading the file: {e}"))
            return

        try:
            # Step 1: Clear Existing Data and Reset Counters
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("TRUNCATE TABLE api_pregunta RESTART IDENTITY CASCADE;")
                cursor.execute("TRUNCATE TABLE api_cuestionario RESTART IDENTITY CASCADE;")
                cursor.execute("TRUNCATE TABLE api_constructo RESTART IDENTITY CASCADE;")
                cursor.execute("TRUNCATE TABLE api_indicador RESTART IDENTITY CASCADE;")
                cursor.execute("TRUNCATE TABLE api_indicadorconstructo RESTART IDENTITY CASCADE;")

            self.stdout.write(self.style.SUCCESS("Existing data cleared, and counters reset."))

            # Step 2: Convert Scorekey to list of integers
            data['Scorekey'] = data['Scorekey'].apply(lambda x: list(map(int, x.split(','))) if pd.notna(x) else [])

            # Helper function to generate acronyms
            def generate_acronym(description):
                acronym = ''.join(word[0].upper() for word in description.split() if word.isalnum())
                
                return acronym[:4]

            # Step 3: Create Indicators and Split Constructs
            indicator_dict = {}
            construct_dict = {}

            for _, row in data.iterrows():
                indicator_name = row['Category']
                construct_names = row['Subcategory'].split('/')  # Split by "/"
                signo = row.get('Signo', '+')  # Default to '+'

                # Create or get Indicator
                indicador, _ = Indicador.objects.get_or_create(nombre=indicator_name)
                indicator_dict[indicator_name] = indicador

                # Create Constructs
                for construct_name in construct_names:
                    construct_name = construct_name.strip()  # Clean whitespace
                    acronimo =  construct_name[:4].upper() # Generate acronym

                    constructo, created = Constructo.objects.get_or_create(
                        descripcion=construct_name,
                        defaults={
                            'indicador': indicador,
                            #'signo': signo,
                            'acronimo': acronimo
                        }
                    )
                    construct_dict[construct_name] = constructo
                    if created:
                        self.stdout.write(self.style.SUCCESS(f"Created Constructo: {construct_name} with Acronym: {acronimo}"))

                    # Link Indicator and Constructo in IndicadorConstructo table
                    IndicadorConstructo.objects.get_or_create(indicador=indicador, constructo=constructo)
                    #Constructo.objects.get_or_create(descripcion=construct_name)
            cuestionarios_dict = {}
            for _, row in data.iterrows():
                cuestionario_name = row['Cuestionarion']
                construct_names = row['Subcategory'].split('/')  # Extract constructs from Subcategory
                scorekey = row['Scorekey']
                is_value = row['is_value']
                question_text = row['Question']

                # Create or get Cuestionario
                if cuestionario_name not in cuestionarios_dict:
                    cuestionarios_dict[cuestionario_name], _ = Cuestionario.objects.get_or_create(
                        nombre_corto=cuestionario_name,
                        defaults={'nombre_largo': cuestionario_name}
                    )

                cuestionario = cuestionarios_dict[cuestionario_name]

                # Create or get Pregunta
                pregunta, created = Pregunta.objects.get_or_create(
                    cve_pregunta=row['ID_pregunta'],
                    texto_pregunta=question_text,
                    cuestionario=cuestionario,
                    defaults={'scorekey': scorekey, 'is_value': is_value}
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f"Created Pregunta: {question_text}"))

                # Link Pregunta to Constructs
                construct_ids = []
                for idx, construct_name in enumerate(construct_names, start=1):
                    construct_name = construct_name.strip()  # Clean up whitespace
                    if construct_name in construct_dict:
                        constructo = construct_dict[construct_name]  # Retrieve the Constructo object
                        setattr(pregunta, f'cve_const{idx}', constructo)  # Link construct ID to the appropriate field
                        construct_ids.append(constructo.cve_const)  # Append construct ID for debugging
                    else:
                        print(f"Construct '{construct_name}' not found in construct_dict.")

                # Save changes to Pregunta
                pregunta.save()


            self.stdout.write(self.style.SUCCESS('Data upload completed successfully!'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {e}"))
