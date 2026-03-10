from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings


@shared_task(name='workers.tasks.check_sla_breaches')
def check_sla_breaches():
    """Verifica tickets com SLA vencido e marca como breached."""
    from apps.sla.models import TicketSLA

    active_slas = TicketSLA.objects.filter(
        ticket__status__in=['open', 'in_progress', 'waiting']
    ).select_related('ticket', 'ticket__company', 'ticket__assigned_to')

    breached_count = 0
    for sla in active_slas:
        if sla.check_breach():
            breached_count += 1
            notify_sla_breach.delay(sla.ticket.pk)

    return f'{breached_count} SLAs marcados como estourados.'


@shared_task(name='workers.tasks.send_sla_warnings')
def send_sla_warnings():
    """Envia avisos para tickets que vencerão em menos de 1h."""
    from apps.sla.models import TicketSLA
    from apps.notifications.models import Notification

    now = timezone.now()
    warning_threshold = now + timezone.timedelta(hours=1)

    slas_near_breach = TicketSLA.objects.filter(
        ticket__status__in=['open', 'in_progress', 'waiting'],
        resolution_deadline__lte=warning_threshold,
        resolution_deadline__gt=now,
        resolution_breached=False,
    ).select_related('ticket', 'ticket__assigned_to', 'ticket__company')

    notified = 0
    for sla in slas_near_breach:
        ticket = sla.ticket
        remaining = sla.resolution_remaining
        minutes = int(remaining.total_seconds() / 60)

        if ticket.assigned_to:
            Notification.objects.get_or_create(
                user=ticket.assigned_to,
                ticket=ticket,
                title=f'SLA expirando em {minutes} minutos — #{ticket.number}',
                defaults={
                    'message': f'O ticket {ticket.subject} ({ticket.company}) vence em {minutes} minutos.',
                    'type': 'warning',
                },
            )
            notified += 1

    return f'{notified} avisos de SLA enviados.'


@shared_task(name='workers.tasks.notify_sla_breach')
def notify_sla_breach(ticket_id):
    """Notifica analistas quando SLA é estourado."""
    from apps.tickets.models import Ticket
    from apps.notifications.models import Notification
    from apps.accounts.models import User

    try:
        ticket = Ticket.objects.select_related('company', 'assigned_to').get(pk=ticket_id)
    except Ticket.DoesNotExist:
        return

    admins = User.objects.filter(role__in=('admin', 'analyst'), is_active=True)
    for user in admins:
        Notification.objects.create(
            user=user,
            ticket=ticket,
            title=f'SLA ESTOURADO — #{ticket.number}',
            message=f'{ticket.company}: {ticket.subject}',
            type='danger',
        )

    # Email para responsável
    if ticket.assigned_to and ticket.assigned_to.email:
        send_sla_breach_email.delay(ticket_id, ticket.assigned_to.email)


@shared_task(name='workers.tasks.send_sla_breach_email')
def send_sla_breach_email(ticket_id, email):
    from apps.tickets.models import Ticket
    try:
        ticket = Ticket.objects.get(pk=ticket_id)
        send_mail(
            subject=f'[URGENTE] SLA Estourado — Ticket #{ticket.number}',
            message=(
                f'O ticket #{ticket.number} ultrapassou o prazo de resolução.\n\n'
                f'Empresa: {ticket.company}\n'
                f'Assunto: {ticket.subject}\n'
                f'Status: {ticket.get_status_display()}\n\n'
                'Acesse o sistema e priorize este atendimento.'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=True,
        )
    except Exception:
        pass


@shared_task(name='workers.tasks.send_ticket_notification_email')
def send_ticket_notification_email(ticket_id, recipient_email, subject, message):
    """Genérico: envia email de notificação de ticket."""
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[recipient_email],
        fail_silently=True,
    )


@shared_task(name='workers.tasks.auto_close_resolved_tickets')
def auto_close_resolved_tickets():
    """Fecha automaticamente tickets resolvidos há mais de 7 dias sem resposta."""
    from apps.tickets.models import Ticket

    cutoff = timezone.now() - timezone.timedelta(days=7)
    tickets = Ticket.objects.filter(status='resolved', updated_at__lte=cutoff)
    count = tickets.update(status='closed')
    return f'{count} tickets fechados automaticamente.'
