from django.db import models
from core.models import TimestampedModel


class Company(TimestampedModel):
    name = models.CharField(max_length=255, verbose_name='Razão Social')
    trade_name = models.CharField(max_length=255, blank=True, verbose_name='Nome Fantasia')
    cnpj = models.CharField(max_length=18, unique=True, verbose_name='CNPJ')
    email = models.EmailField(verbose_name='E-mail')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Telefone')
    address = models.TextField(blank=True, verbose_name='Endereço')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    logo_url = models.URLField(blank=True)

    # Configuração de SLA personalizado por empresa
    sla_response_hours = models.IntegerField(
        default=4,
        verbose_name='SLA Resposta (horas)'
    )
    sla_resolution_hours = models.IntegerField(
        default=24,
        verbose_name='SLA Resolução (horas)'
    )

    class Meta:
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'
        ordering = ['name']

    def __str__(self):
        return self.name
