from rest_framework import permissions
from django.contrib.auth.models import User

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