# scripts/initialize_permissions.py

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from api.models import ScoreConstructo, ScoreIndicador, Reporte  # Ajusta 'myapp' al nombre de tu aplicación

def create_groups_and_permissions():
    # Crear grupos
    superusers = Group.objects.create(name='Superusers')
    admin = Group.objects.create(name='Administradores')
    coordinador_tutorias_nacional = Group.objects.create(name='Coordinador  de Tutorias a Nivel Nacional')
    coordinador_tutorias_region = Group.objects.create(name='Coordinador  de Tutorias a Nivel Region')
    coordinador_tutorias_intitucion = Group.objects.create(name='Coordinador de Tutorias por Institucion')
    coordinador_departamento= Group.objects.create(name='Coordinador de Tutorias por Departamento')
    coordinador_plan_estudios = Group.objects.create(name='Coordinador de Plan de Estudios')
    Tutores = Group.objects.create(name='Tutores')

    # Definir permisos
    permisos = {
        'add_scoreconstructo': 'Can add score constructo',
        'change_scoreconstructo': 'Can change score constructo',
        'delete_scoreconstructo': 'Can delete score constructo',
        'view_scoreconstructo': 'Can view score constructo',
        'add_scoreindicador': 'Can add score indicador',
        'change_scoreindicador': 'Can change score indicador',
        'delete_scoreindicador': 'Can delete score indicador',
        'view_scoreindicador': 'Can view score indicador',
        'view_reporte': 'Can view reporte',
        'view_retrochatgpt': 'Can view retrochatgpt',
        'add_respuesta': 'Can add respuesta',
        'view_cuestionario': 'Can view cuestinoario',
    }

    # Asignar permisos a grupos
    for codename, name in permisos.items():
        permission = Permission.objects.get(codename=codename)
        superusers.permissions.add(permission)
        coordinador_departamento.permissions.add(permission)
        coordinador_tutorias_intitucion.permissions.add(permission)
        coordinador_tutorias_region.permissions.add(permission)
        coordinador_tutorias_nacional.permissions.add(permission)
        coordinador_plan_estudios.permissions.add(permission)
        Tutores.permissions.add(permission)

    # Asignar permisos específicos a grupos

    
    

    # Coordinador  de Tutorias a Nivel Nacional
    coordinador_tutorias_nacional.permissions.clear()
    coordinador_tutorias_nacional.permissions.add(Permission.objects.get(codename='view_scoreconstructo'))
    coordinador_tutorias_nacional.permissions.add(Permission.objects.get(codename='view_scoreindicador'))
    coordinador_tutorias_nacional.permissions.add(Permission.objects.get(codename='view_reporte'))

    # Coordinador  de Tutorias a Nivel Región
    coordinador_tutorias_region.permissions.clear()
    #coordinador_tutorias_region.permissions.add(Permission.objects.get(codename='view_scoreconstructo'))
    #coordinador_tutorias_region.permissions.add(Permission.objects.get(codename='view_scoreindicador'))
    coordinador_tutorias_region.permissions.add(Permission.objects.get(codename='view_reporte'))
    
    # Coordinador  de Tutorias por Institución
    coordinador_tutorias_intitucion.permissions.clear()
    #coordinador_tutorias_intitucion.permissions.add(Permission.objects.get(codename='view_scoreconstructo'))
    #coordinador_tutorias_intitucion.permissions.add(Permission.objects.get(codename='view_scoreindicador'))
    coordinador_tutorias_intitucion.permissions.add(Permission.objects.get(codename='view_reporte'))

    # Coordinador de Tutorias por Departamento
    """coordinador_departamento.permissions.remove(Permission.objects.get(codename='add_scoreconstructo'))
    coordinador_departamento.permissions.remove(Permission.objects.get(codename='delete_scoreconstructo'))
    coordinador_departamento.permissions.remove(Permission.objects.get(codename='add_scoreindicador'))
    coordinador_departamento.permissions.remove(Permission.objects.get(codename='delete_scoreindicador'))"""
    coordinador_departamento.permissions.add(Permission.objects.get(codename='view_reporte'))

    # Coordinador de Plan de Estudios
    coordinador_plan_estudios.permissions.clear()
    #coordinador_plan_estudios.permissions.add(Permission.objects.get(codename='view_scoreconstructo'))
    #coordinador_plan_estudios.permissions.add(Permission.objects.get(codename='view_scoreindicador'))
    coordinador_plan_estudios.permissions.add(Permission.objects.get(codename='view_reporte'))
    #coordinador_plan_estudios.permissions.add(Permission.objects.get(codename='view_retrochatgpt'))
    
    # Tutores
    Tutores.permissions.clear()
    Tutores.permissions.add(Permission.objects.get(codename='add_respuesta'))
    Tutores.permissions.add(Permission.objects.get(codename='view_cuestionario'))
    Tutores.permissions.add(Permission.objects.get(codename='view_retrochatgpt'))
    
# Ejecutar la función    
create_groups_and_permissions()