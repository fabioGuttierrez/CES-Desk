from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Q
from django.utils import timezone

from apps.tickets.models import Ticket, TicketCategory, TicketMessage
from apps.accounts.models import User
from apps.sla.models import TicketSLA
from apps.attachments.models import Attachment
from apps.notifications.models import Notification
from core.permissions import IsAdmin, IsAnalyst


@login_required
def dashboard(request):
    user = request.user

    if user.role == 'client':
        return redirect('client_dashboard')

    # Métricas para analistas/admin
    tickets_qs = Ticket.objects.all()
    total = tickets_qs.count()
    open_count = tickets_qs.filter(status='open').count()
    in_progress = tickets_qs.filter(status='in_progress').count()
    resolved_today = tickets_qs.filter(
        status='resolved',
        updated_at__date=timezone.now().date()
    ).count()
    urgent = tickets_qs.filter(priority='urgent', status__in=['open', 'in_progress']).count()
    sla_breached = TicketSLA.objects.filter(
        resolution_breached=True,
        ticket__status__in=['open', 'in_progress', 'waiting']
    ).count()

    recent_tickets = tickets_qs.select_related(
        'company', 'created_by', 'assigned_to', 'category'
    ).order_by('-created_at')[:10]

    tickets_by_status = {
        'open': tickets_qs.filter(status='open'),
        'waiting': tickets_qs.filter(status='waiting'),
        'in_progress': tickets_qs.filter(status='in_progress'),
        'resolved': tickets_qs.filter(status='resolved'),
    }

    notifications = Notification.objects.filter(user=user, read=False).order_by('-created_at')[:5]

    context = {
        'total': total,
        'open_count': open_count,
        'in_progress': in_progress,
        'resolved_today': resolved_today,
        'urgent': urgent,
        'sla_breached': sla_breached,
        'recent_tickets': recent_tickets,
        'tickets_by_status': tickets_by_status,
        'notifications': notifications,
    }
    return render(request, 'admin/dashboard.html', context)


@login_required
def client_dashboard(request):
    user = request.user
    tickets = Ticket.objects.filter(company=user.company).select_related(
        'category', 'assigned_to'
    ).order_by('-created_at')

    notifications = Notification.objects.filter(user=user, read=False)[:5]

    context = {
        'tickets': tickets,
        'notifications': notifications,
        'open_count': tickets.filter(status__in=['open', 'in_progress', 'waiting']).count(),
    }
    return render(request, 'client/dashboard.html', context)


@login_required
def ticket_list(request):
    user = request.user

    if user.role == 'client':
        qs = Ticket.objects.filter(company=user.company)
    else:
        qs = Ticket.objects.all()

    # Filtros
    status = request.GET.get('status')
    priority = request.GET.get('priority')
    category = request.GET.get('category')
    search = request.GET.get('q')

    if status:
        qs = qs.filter(status=status)
    if priority:
        qs = qs.filter(priority=priority)
    if category:
        qs = qs.filter(category_id=category)
    if search:
        qs = qs.filter(Q(subject__icontains=search) | Q(number__icontains=search))

    qs = qs.select_related('company', 'created_by', 'assigned_to', 'category').order_by('-created_at')
    categories = TicketCategory.objects.filter(is_active=True)

    context = {
        'tickets': qs,
        'categories': categories,
        'current_status': status,
        'current_priority': priority,
    }
    template = 'client/ticket_list.html' if user.role == 'client' else 'admin/ticket_list.html'
    return render(request, template, context)


@login_required
def ticket_detail(request, pk):
    user = request.user
    ticket = get_object_or_404(Ticket, pk=pk)

    # Verificação de acesso por empresa
    if user.role == 'client' and ticket.company != user.company:
        messages.error(request, 'Acesso negado.')
        return redirect('ticket_list')

    messages_qs = ticket.messages.all()
    if user.role == 'client':
        messages_qs = messages_qs.filter(is_internal=False)

    analysts = User.objects.filter(role__in=('admin', 'analyst'), is_active=True)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'reply':
            msg_text = request.POST.get('message', '').strip()
            is_internal = request.POST.get('is_internal') == 'on' and user.is_analyst

            if msg_text:
                msg = TicketMessage.objects.create(
                    ticket=ticket,
                    author=user,
                    message=msg_text,
                    is_internal=is_internal,
                )
                # Atualiza status
                if user.role == 'client' and ticket.status == 'waiting':
                    ticket.status = 'open'
                    ticket.save(update_fields=['status'])
                elif user.role in ('admin', 'analyst') and ticket.status == 'open':
                    ticket.status = 'in_progress'
                    ticket.save(update_fields=['status'])

                # Processa anexos
                files = request.FILES.getlist('attachments')
                for f in files:
                    file_url = _upload_to_supabase(f, ticket)
                    Attachment.objects.create(
                        ticket=ticket,
                        message=msg,
                        uploaded_by=user,
                        file_url=file_url,
                        file_name=f.name,
                        file_size=f.size,
                        content_type=f.content_type,
                    )
                messages.success(request, 'Mensagem enviada.')

        elif action == 'assign' and user.is_analyst:
            analyst_id = request.POST.get('analyst_id')
            ticket.assigned_to_id = analyst_id
            ticket.status = 'in_progress'
            ticket.save(update_fields=['assigned_to', 'status'])
            messages.success(request, 'Ticket atribuído.')

        elif action == 'change_status' and user.is_analyst:
            new_status = request.POST.get('status')
            if new_status in dict(Ticket.STATUS_CHOICES):
                ticket.status = new_status
                ticket.save(update_fields=['status'])
                if new_status in ('resolved', 'closed'):
                    try:
                        ticket.sla.resolved_at = timezone.now()
                        ticket.sla.save(update_fields=['resolved_at'])
                    except Exception:
                        pass
                messages.success(request, 'Status atualizado.')

        elif action == 'change_priority' and user.is_analyst:
            new_priority = request.POST.get('priority')
            if new_priority in dict(Ticket.PRIORITY_CHOICES):
                ticket.priority = new_priority
                ticket.save(update_fields=['priority'])
                messages.success(request, 'Prioridade atualizada.')

        return redirect('ticket_detail', pk=ticket.pk)

    context = {
        'ticket': ticket,
        'messages': messages_qs,
        'analysts': analysts,
        'attachments': ticket.attachments.all(),
        'status_choices': Ticket.STATUS_CHOICES,
        'priority_choices': Ticket.PRIORITY_CHOICES,
    }
    template = 'client/ticket_detail.html' if user.role == 'client' else 'admin/ticket_detail.html'
    return render(request, template, context)


@login_required
def ticket_create(request):
    categories = TicketCategory.objects.filter(is_active=True)

    if request.method == 'POST':
        subject = request.POST.get('subject', '').strip()
        description = request.POST.get('description', '').strip()
        category_id = request.POST.get('category')
        priority = request.POST.get('priority', 'medium')

        if not subject or not description:
            messages.error(request, 'Preencha assunto e descrição.')
            return render(request, 'client/ticket_create.html', {'categories': categories})

        user = request.user
        company = user.company

        ticket = Ticket.objects.create(
            company=company,
            created_by=user,
            category_id=category_id or None,
            subject=subject,
            description=description,
            priority=priority,
        )

        files = request.FILES.getlist('attachments')
        for f in files:
            file_url = _upload_to_supabase(f, ticket)
            Attachment.objects.create(
                ticket=ticket,
                uploaded_by=user,
                file_url=file_url,
                file_name=f.name,
                file_size=f.size,
                content_type=f.content_type,
            )

        messages.success(request, f'Chamado #{ticket.number} aberto com sucesso!')
        return redirect('ticket_detail', pk=ticket.pk)

    context = {
        'categories': categories,
        'priority_choices': Ticket.PRIORITY_CHOICES,
    }
    return render(request, 'client/ticket_create.html', context)


@login_required
def kanban(request):
    if request.user.role == 'client':
        return redirect('ticket_list')

    statuses = [
        ('open', 'Aberto'),
        ('in_progress', 'Em Atendimento'),
        ('waiting', 'Aguardando Cliente'),
        ('resolved', 'Resolvido'),
    ]
    columns = {
        s: Ticket.objects.filter(status=s).select_related('company', 'assigned_to', 'category')
        for s, _ in statuses
    }
    return render(request, 'admin/kanban.html', {
        'statuses': statuses,
        'columns': columns,
    })


@login_required
def kanban_move(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'method not allowed'}, status=405)
    if request.user.role == 'client':
        return JsonResponse({'error': 'forbidden'}, status=403)

    valid_statuses = {'open', 'in_progress', 'waiting', 'resolved'}
    ticket_id = request.POST.get('ticket_id')
    new_status = request.POST.get('status')

    if new_status not in valid_statuses:
        return JsonResponse({'error': 'invalid status'}, status=400)

    ticket = get_object_or_404(Ticket, pk=ticket_id)
    ticket.status = new_status
    ticket.save(update_fields=['status'])
    return JsonResponse({'ok': True})


@login_required
def notifications_mark_read(request):
    Notification.objects.filter(user=request.user, read=False).update(read=True)
    return JsonResponse({'status': 'ok'})


@login_required
def holiday_list(request):
    if request.user.role != 'admin':
        return redirect('dashboard')
    from apps.sla.models import Holiday
    holidays = Holiday.objects.all()
    return render(request, 'admin/holidays.html', {'holidays': holidays})


@login_required
def holiday_create(request):
    if request.user.role != 'admin':
        return redirect('dashboard')
    if request.method == 'POST':
        from apps.sla.models import Holiday
        date = request.POST.get('date')
        name = request.POST.get('name', '').strip()
        if date and name:
            Holiday.objects.get_or_create(date=date, defaults={'name': name})
        return redirect('holiday_list')
    return redirect('holiday_list')


@login_required
def holiday_delete(request, pk):
    if request.user.role != 'admin':
        return redirect('dashboard')
    from apps.sla.models import Holiday
    Holiday.objects.filter(pk=pk).delete()
    return redirect('holiday_list')


def _upload_to_supabase(file, ticket):
    """Faz upload do arquivo para Supabase Storage e retorna URL pública."""
    try:
        from django.conf import settings
        from supabase import create_client

        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        path = f'tickets/{ticket.number}/{file.name}'
        supabase.storage.from_(settings.SUPABASE_BUCKET).upload(
            path,
            file.read(),
            {'content-type': file.content_type},
        )
        url = supabase.storage.from_(settings.SUPABASE_BUCKET).get_public_url(path)
        return url
    except Exception:
        # Fallback: salvar localmente se Supabase não configurado
        from django.core.files.storage import default_storage
        path = default_storage.save(f'uploads/{file.name}', file)
        return default_storage.url(path)
