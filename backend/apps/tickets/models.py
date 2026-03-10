from django.db import models
from core.models import TimestampedModel


class TicketCategory(models.Model):
    name = models.CharField(max_length=100, verbose_name='Nome')
    description = models.TextField(blank=True, verbose_name='Descrição')
    icon = models.CharField(max_length=50, blank=True, default='📋')
    sla_hours = models.IntegerField(default=24, verbose_name='SLA Padrão (horas)')
    auto_response = models.TextField(
        blank=True,
        verbose_name='Resposta Automática',
        help_text='Mensagem enviada ao cliente ao abrir chamado nessa categoria',
    )
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Ticket(TimestampedModel):
    STATUS_OPEN = 'open'
    STATUS_WAITING = 'waiting'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_RESOLVED = 'resolved'
    STATUS_CLOSED = 'closed'

    STATUS_CHOICES = (
        (STATUS_OPEN, 'Aberto'),
        (STATUS_WAITING, 'Aguardando Cliente'),
        (STATUS_IN_PROGRESS, 'Em Atendimento'),
        (STATUS_RESOLVED, 'Resolvido'),
        (STATUS_CLOSED, 'Fechado'),
    )

    PRIORITY_LOW = 'low'
    PRIORITY_MEDIUM = 'medium'
    PRIORITY_HIGH = 'high'
    PRIORITY_URGENT = 'urgent'

    PRIORITY_CHOICES = (
        (PRIORITY_LOW, 'Baixa'),
        (PRIORITY_MEDIUM, 'Média'),
        (PRIORITY_HIGH, 'Alta'),
        (PRIORITY_URGENT, 'Urgente'),
    )

    # Número sequencial amigável
    number = models.CharField(max_length=20, unique=True, blank=True)

    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='tickets',
        verbose_name='Empresa',
    )
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='created_tickets',
        verbose_name='Aberto por',
    )
    assigned_to = models.ForeignKey(
        'accounts.User',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='assigned_tickets',
        verbose_name='Responsável',
    )
    category = models.ForeignKey(
        TicketCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name='tickets',
        verbose_name='Categoria',
    )
    subject = models.CharField(max_length=255, verbose_name='Assunto')
    description = models.TextField(verbose_name='Descrição')
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default=PRIORITY_MEDIUM,
        verbose_name='Prioridade',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_OPEN,
        verbose_name='Status',
    )
    tags = models.CharField(max_length=255, blank=True, verbose_name='Tags')

    class Meta:
        verbose_name = 'Ticket'
        verbose_name_plural = 'Tickets'
        ordering = ['-created_at']

    def __str__(self):
        return f'#{self.number} — {self.subject}'

    def save(self, *args, **kwargs):
        if not self.number:
            last = Ticket.objects.order_by('-id').first()
            next_id = (last.id + 1) if last else 1
            self.number = f'DP{next_id:05d}'
        super().save(*args, **kwargs)

    @property
    def is_open(self):
        return self.status not in (self.STATUS_RESOLVED, self.STATUS_CLOSED)

    @property
    def priority_badge_class(self):
        classes = {
            'low': 'badge-success',
            'medium': 'badge-info',
            'high': 'badge-warning',
            'urgent': 'badge-danger',
        }
        return classes.get(self.priority, 'badge-secondary')

    @property
    def status_badge_class(self):
        classes = {
            'open': 'badge-primary',
            'waiting': 'badge-warning',
            'in_progress': 'badge-info',
            'resolved': 'badge-success',
            'closed': 'badge-secondary',
        }
        return classes.get(self.status, 'badge-secondary')


class TicketMessage(TimestampedModel):
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='Ticket',
    )
    author = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='Autor',
    )
    message = models.TextField(verbose_name='Mensagem')
    is_internal = models.BooleanField(
        default=False,
        verbose_name='Nota Interna',
        help_text='Notas internas não são vistas pelo cliente',
    )

    class Meta:
        verbose_name = 'Mensagem'
        verbose_name_plural = 'Mensagens'
        ordering = ['created_at']

    def __str__(self):
        return f'Msg #{self.pk} — Ticket #{self.ticket.number}'
