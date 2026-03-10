from django.db import models
from django.utils import timezone


class Holiday(models.Model):
    """Feriado nacional/estadual/municipal que suspende o cômputo do SLA."""
    date = models.DateField(unique=True, verbose_name='Data')
    name = models.CharField(max_length=120, verbose_name='Descrição')

    class Meta:
        verbose_name = 'Feriado'
        verbose_name_plural = 'Feriados'
        ordering = ['date']

    def __str__(self):
        return f'{self.date:%d/%m/%Y} — {self.name}'


class TicketSLA(models.Model):
    ticket = models.OneToOneField(
        'tickets.Ticket',
        on_delete=models.CASCADE,
        related_name='sla',
    )
    response_deadline = models.DateTimeField(verbose_name='Prazo de Resposta')
    resolution_deadline = models.DateTimeField(verbose_name='Prazo de Resolução')
    responded_at = models.DateTimeField(null=True, blank=True, verbose_name='Respondido em')
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name='Resolvido em')
    response_breached = models.BooleanField(default=False, verbose_name='SLA Resposta Estourado')
    resolution_breached = models.BooleanField(default=False, verbose_name='SLA Resolução Estourado')

    class Meta:
        verbose_name = 'SLA'
        verbose_name_plural = 'SLAs'

    def __str__(self):
        return f'SLA Ticket #{self.ticket.number}'

    @property
    def response_status(self):
        if self.responded_at:
            breached = self.responded_at > self.response_deadline
            return 'breached' if breached else 'ok'
        if timezone.now() > self.response_deadline:
            return 'breached'
        return 'pending'

    @property
    def resolution_status(self):
        if self.resolved_at:
            breached = self.resolved_at > self.resolution_deadline
            return 'breached' if breached else 'ok'
        if timezone.now() > self.resolution_deadline:
            return 'breached'
        return 'pending'

    @property
    def resolution_remaining(self):
        """Retorna timedelta até vencer (negativo se já venceu)."""
        return self.resolution_deadline - timezone.now()

    def check_breach(self):
        now = timezone.now()
        changed = False
        if not self.responded_at and now > self.response_deadline:
            self.response_breached = True
            changed = True
        if not self.resolved_at and now > self.resolution_deadline:
            self.resolution_breached = True
            changed = True
        if changed:
            self.save(update_fields=['response_breached', 'resolution_breached'])
        return changed
