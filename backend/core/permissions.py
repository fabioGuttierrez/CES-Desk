from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'


class IsAnalyst(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ('admin', 'analyst')


class IsClient(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'client'


class IsOwnerOrAnalyst(BasePermission):
    """Cliente só acessa seus próprios recursos; analistas/admin acessam tudo."""
    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.role in ('admin', 'analyst'):
            return True
        # Para tickets/attachments com campo company
        if hasattr(obj, 'company') and user.company:
            return obj.company == user.company
        # Para mensagens
        if hasattr(obj, 'author'):
            return obj.author == user
        return False


class ReadOnlyOrAnalyst(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_authenticated and request.user.role in ('admin', 'analyst')
