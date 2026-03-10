from django.db import models
from core.models import TimestampedModel


class Attachment(TimestampedModel):
    ticket = models.ForeignKey(
        'tickets.Ticket',
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name='Ticket',
    )
    message = models.ForeignKey(
        'tickets.TicketMessage',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='attachments',
        verbose_name='Mensagem',
    )
    uploaded_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name='Enviado por',
    )
    file_url = models.URLField(verbose_name='URL do Arquivo')
    file_name = models.CharField(max_length=255, verbose_name='Nome do Arquivo')
    file_size = models.IntegerField(default=0, verbose_name='Tamanho (bytes)')
    content_type = models.CharField(max_length=100, blank=True, verbose_name='Tipo')

    class Meta:
        verbose_name = 'Anexo'
        verbose_name_plural = 'Anexos'
        ordering = ['-created_at']

    def __str__(self):
        return self.file_name

    @property
    def file_size_display(self):
        if self.file_size < 1024:
            return f'{self.file_size} B'
        elif self.file_size < 1024 ** 2:
            return f'{self.file_size / 1024:.1f} KB'
        else:
            return f'{self.file_size / (1024 ** 2):.1f} MB'
