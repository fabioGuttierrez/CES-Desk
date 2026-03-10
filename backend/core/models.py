from django.db import models


class TimestampedModel(models.Model):
    """Base model com timestamps automáticos."""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class CompanyScopedModel(TimestampedModel):
    """Base para modelos com escopo por empresa (multitenancy)."""
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='%(class)ss',
    )

    class Meta:
        abstract = True
