from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import Group
from api.models import CustomUser, Region, Instituto, Departamento, Carrera

class Command(BaseCommand):
    help = "Crear un usuario, asignarlo a un grupo y vincularlo a otras entidades"

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, required=True, help="Correo electrónico del usuario")
        parser.add_argument('--password', type=str, required=True, help="Contraseña del usuario")
        parser.add_argument('--group', type=str, required=True, help="Nombre del grupo")
        parser.add_argument('--region', type=int, help="Clave primaria (cve_region) de la región")
        parser.add_argument('--instituto', type=int, help="Clave primaria (cve_inst) del instituto")
        parser.add_argument('--departamento', type=int, help="Clave primaria (cve_depto) del departamento")
        parser.add_argument('--carrera', type=int, help="Clave primaria (cve_carrera) de la carrera")

    def handle(self, *args, **kwargs):
        email = kwargs['email']
        password = kwargs['password']
        group_name = kwargs['group']
        region_id = kwargs.get('region')
        instituto_id = kwargs.get('instituto')
        departamento_id = kwargs.get('departamento')
        carrera_id = kwargs.get('carrera')

        try:
            # Crear o verificar grupo
            group, _ = Group.objects.get_or_create(name=group_name)
            self.stdout.write(self.style.SUCCESS(f"Grupo '{group_name}' verificado o creado."))

            # Obtener relaciones
            region = Region.objects.get(cve_region=region_id) if region_id else None
            instituto = Instituto.objects.get(cve_inst=instituto_id) if instituto_id else None
            departamento = Departamento.objects.get(cve_depto=departamento_id) if departamento_id else None
            carrera = Carrera.objects.get(cve_carrera=carrera_id) if carrera_id else None

            # Crear usuario
            user = CustomUser.objects.create_user(
                email=email,
                password=password,
                region=region,
                instituto=instituto,
                departamento=departamento,
                carrera=carrera,
            )

            # Asignar grupo al usuario
            user.groups.add(group)
            self.stdout.write(self.style.SUCCESS(f"Usuario '{email}' creado y asignado al grupo '{group_name}'."))

        except Group.DoesNotExist:
            raise CommandError(f"El grupo '{group_name}' no existe.")
        except Region.DoesNotExist:
            raise CommandError(f"La región con clave '{region_id}' no existe.")
        except Instituto.DoesNotExist:
            raise CommandError(f"El instituto con clave '{instituto_id}' no existe.")
        except Departamento.DoesNotExist:
            raise CommandError(f"El departamento con clave '{departamento_id}' no existe.")
        except Carrera.DoesNotExist:
            raise CommandError(f"La carrera con clave '{carrera_id}' no existe.")
        except Exception as e:
            raise CommandError(f"Error al crear el usuario: {str(e)}")

        self.stdout.write(self.style.SUCCESS(f"Usuario '{email}' creado exitosamente."))
