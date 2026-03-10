from django.db import models
from core.models import TimestampedModel


class Notification(TimestampedModel):
    TYPE_INFO = 'info'
    TYPE_SUCCESS = 'success'
    TYPE_WARNING = 'warning'
    TYPE_DANGER = 'danger'

    TYPE_CHOICES = (
        (TYPE_INFO, 'Informação'),
        (TYPE_SUCCESS, 'Sucesso'),
        (TYPE_WARNING, 'Aviso'),
        (TYPE_DANGER, 'Urgente'),
    )

    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    ticket = models.ForeignKey(
        'tickets.Ticket',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications',
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default=TYPE_INFO)
    read = models.BooleanField(default=False)
    sent_email = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Notificação'
        verbose_name_plural = 'Notificações'
        ordering = ['-created_at']

    def __str__(self):
        return self.title
