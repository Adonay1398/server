import random
from django.core.management.base import BaseCommand
from api.models import Cuestionario, Pregunta, Respuesta, CustomUser, DatosAplicacion


class Command(BaseCommand):
    help = 'Generate random responses for a given user and questionnaire.'

    def add_arguments(self, parser):
        parser.add_argument('user_id', type=int, help='The ID of the user.')
        parser.add_argument('cuestionario_id', type=int, help='The ID of the questionnaire.')
        parser.add_argument('aplicacion_id', type=int, help='The ID of the application (cve_aplic).')
        parser.add_argument('--num_responses', type=int, default=1, help='Number of sets of random responses to generate.')

    def handle(self, *args, **kwargs):
        user_id = kwargs['user_id']
        cuestionario_id = kwargs['cuestionario_id']
        aplicacion_id = kwargs['aplicacion_id']
        num_responses = kwargs['num_responses']

        try:
            # Retrieve the user, questionnaire, and application
            user = CustomUser.objects.get(id=user_id)
            cuestionario = Cuestionario.objects.get(cve_cuestionario=cuestionario_id)
            aplicacion = DatosAplicacion.objects.get(cve_aplic=aplicacion_id)

            # Retrieve all questions in the questionnaire
            preguntas = Pregunta.objects.filter(cuestionario=cuestionario)

            if not preguntas.exists():
                self.stdout.write(self.style.ERROR("No questions found for the specified questionnaire."))
                return

            self.stdout.write(self.style.SUCCESS(f"Generating {num_responses} sets of random responses for user '{user.username}' on questionnaire '{cuestionario.nombre_corto}'."))

            for _ in range(num_responses):
                for pregunta in preguntas:
                    # Check if a response already exists
                    response_exists = Respuesta.objects.filter(
                        user=user,
                        pregunta=pregunta,
                        cve_aplic=aplicacion
                    ).exists()

                    if response_exists:
                        self.stdout.write(self.style.WARNING(
                            f"Response already exists for question '{pregunta.texto_pregunta}'. Skipping."
                        ))
                        continue

                    # Generate a random response value (assuming the range is 1-5 for this example)
                    valor = random.randint(1, 5)

                    # Save the response
                    Respuesta.objects.create(
                        user=user,
                        pregunta=pregunta,
                        valor=valor,
                        cve_aplic=aplicacion  # Set the cve_aplic field
                    )

                    self.stdout.write(self.style.SUCCESS(f"Saved response for question '{pregunta.texto_pregunta}': {valor}"))

            self.stdout.write(self.style.SUCCESS("Random responses generated successfully!"))

        except CustomUser.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"User with ID {user_id} does not exist."))
        except Cuestionario.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Questionnaire with ID {cuestionario_id} does not exist."))
        except DatosAplicacion.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Application with ID {aplicacion_id} does not exist."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {e}"))
