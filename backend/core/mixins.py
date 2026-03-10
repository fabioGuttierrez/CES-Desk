class CompanyScopedMixin:
    """
    Filtra automaticamente querysets pelo company do usuário logado.
    Para analistas/admin, permite filtrar por company explicitamente.
    """
    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.role == 'client' and user.company:
            return qs.filter(company=user.company)
        company_id = self.request.query_params.get('company_id')
        if company_id and user.role in ('admin', 'analyst'):
            return qs.filter(company_id=company_id)
        return qs


class AuditMixin:
    """Registra ações de criação/atualização no AuditLog."""
    def perform_create(self, serializer):
        instance = serializer.save()
        self._log_action('CREATE', instance)

    def perform_update(self, serializer):
        instance = serializer.save()
        self._log_action('UPDATE', instance)

    def perform_destroy(self, instance):
        self._log_action('DELETE', instance)
        instance.delete()

    def _log_action(self, action, instance):
        from apps.audit.models import AuditLog
        AuditLog.objects.create(
            user=self.request.user,
            action=action,
            model=instance.__class__.__name__,
            object_id=str(instance.pk),
            details=str(instance),
        )
