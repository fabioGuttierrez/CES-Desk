from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Ticket, TicketMessage


@receiver(post_save, sender=Ticket)
def on_ticket_created(sender, instance, created, **kwargs):
    """Cria SLA, envia notificação e resposta automática ao criar ticket."""
    if created:
        _create_sla(instance)
        _notify_analysts(instance)
        _send_auto_response(instance)


def _create_sla(ticket):
    from apps.sla.models import TicketSLA
    from apps.sla.utils import add_business_days
    company = ticket.company
    category = ticket.category

    response_hours = category.sla_hours if category else company.sla_response_hours
    resolution_hours = company.sla_resolution_hours

    TicketSLA.objects.create(
        ticket=ticket,
        response_deadline=add_business_days(ticket.created_at, response_hours),
        resolution_deadline=add_business_days(ticket.created_at, resolution_hours),
    )


def _notify_analysts(ticket):
    from apps.notifications.models import Notification
    from apps.accounts.models import User

    analysts = User.objects.filter(role__in=('admin', 'analyst'), is_active=True)
    notifications = [
        Notification(
            user=analyst,
            ticket=ticket,
            title=f'Novo ticket #{ticket.number}',
            message=f'{ticket.company} abriu: {ticket.subject}',
            type=Notification.TYPE_INFO,
        )
        for analyst in analysts
    ]
    Notification.objects.bulk_create(notifications)


def _send_auto_response(ticket):
    """Envia resposta automática da categoria, se configurada."""
    if ticket.category and ticket.category.auto_response:
        from apps.accounts.models import User
        try:
            system_user = User.objects.filter(is_superuser=True).first()
            if system_user:
                TicketMessage.objects.create(
                    ticket=ticket,
                    author=system_user,
                    message=ticket.category.auto_response,
                    is_internal=False,
                )
        except Exception:
            pass


@receiver(post_save, sender=TicketMessage)
def on_message_created(sender, instance, created, **kwargs):
    """Notifica partes ao receber nova mensagem."""
    if not created:
        return

    ticket = instance.ticket
    author = instance.author

    if instance.is_internal:
        return

    from apps.notifications.models import Notification

    # Notifica cliente (se mensagem é do analista)
    if author.role in ('admin', 'analyst'):
        Notification.objects.create(
            user=ticket.created_by,
            ticket=ticket,
            title=f'Resposta no ticket #{ticket.number}',
            message=f'{author.get_full_name() or author.username} respondeu seu chamado.',
            type=Notification.TYPE_INFO,
        )
        # Atualiza SLA
        try:
            sla = ticket.sla
            if not sla.responded_at:
                sla.responded_at = instance.created_at
                sla.save(update_fields=['responded_at'])
        except Exception:
            pass
    else:
        # Notifica analista responsável
        if ticket.assigned_to:
            Notification.objects.create(
                user=ticket.assigned_to,
                ticket=ticket,
                title=f'Resposta do cliente — #{ticket.number}',
                message=f'{ticket.company} respondeu o chamado.',
                type=Notification.TYPE_WARNING,
            )
