from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied


class RoleRequiredMixin(LoginRequiredMixin):
    required_roles = []

    def dispatch(self, request, *args, **kwargs):
        result = super().dispatch(request, *args, **kwargs)
        if not hasattr(request.user, 'profile'):
            raise PermissionDenied
        if self.required_roles and request.user.profile.role not in self.required_roles:
            raise PermissionDenied
        return result


class OwnerRequiredMixin(LoginRequiredMixin):
    owner_field = 'criado_por'

    def get_object(self):
        obj = super().get_object()
        if getattr(obj, self.owner_field) != self.request.user:
            raise PermissionDenied
        return obj
