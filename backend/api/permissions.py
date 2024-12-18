from rest_framework import permissions
from django.contrib.auth.models import User
from rest_framework.permissions import BasePermission

class IsAuthorizedUser(BasePermission):
    def has_permission(self, request, view):
        # Verificar si el usuario pertenece a uno de los grupos autorizados
        authorized_groups = [
            'Coordinador de Tutorias a Nivel Nacional',
            'Coordinador de Tutorias a Nivel Region',
            'Coordinador de Tutorias por Institucion',
            'Coordinador de Tutorias por Departamento',
            'Coordinador de Plan de Estudios',
            'Tutores'
        ]       
        return request.user and request.user.groups.filter(name__in=authorized_groups).exists()
class IsOwner(permissions.BasePermission):
    """
    Permiso personalizado para permitir solo a los propietarios de un objeto ver o editarlo.
    """

    def has_object_permission(self, request, view, obj):
        # El objeto debe tener un atributo `user` que sea una instancia del usuario autenticado.
        if isinstance(obj, User):
            return obj == request.user
            # Para otros modelos, verifica si el objeto tiene un atributo `user`
            return obj.user == request.user



class IsCoordinadorDeTutoriasNivelNacional(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.groups.filter(name='Coordinador de Tutorias a Nivel Nacional').exists()

class IsCoordinadorDeTutoriasNivelRegion(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.groups.filter(name='Coordinador de Tutorias a Nivel Region').exists()

class IsCoordinadorDeTutoriasPorInstitucion(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.groups.filter(name='Coordinador de Tutorias por Institucion').exists()

class IsCoordinadorDeTutoriasPorDepartamento(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.groups.filter(name='Coordinador de Tutorias por Departamento').exists()

class IsCoordinadorDePlanDeEstudios(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.groups.filter(name='Coordinador de Plan de Estudios').exists()
    
class IsTutor(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.groups.filter(name='Tutores').exists()





