from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages

from apps.accounts.models import User
from apps.companies.models import Company


@login_required
def profile(request):
    user = request.user
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.phone = request.POST.get('phone', user.phone)
        user.save(update_fields=['first_name', 'last_name', 'phone'])
        messages.success(request, 'Perfil atualizado.')
        return redirect('profile')
    return render(request, 'base/profile.html', {'user': user})


@login_required
def forced_password_change(request):
    """Exibida quando must_change_password=True. Usuário define uma nova senha."""
    if not request.user.must_change_password:
        return redirect('dashboard')

    if request.method == 'POST':
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')

        if not password1:
            messages.error(request, 'A senha não pode ser vazia.')
        elif password1 != password2:
            messages.error(request, 'As senhas não conferem.')
        elif len(password1) < 8:
            messages.error(request, 'A senha deve ter no mínimo 8 caracteres.')
        else:
            request.user.set_password(password1)
            request.user.must_change_password = False
            request.user.save(update_fields=['password', 'must_change_password'])
            update_session_auth_hash(request, request.user)
            messages.success(request, 'Senha alterada com sucesso. Bem-vindo!')
            if request.user.role == 'client':
                return redirect('client_dashboard')
            return redirect('dashboard')

    return render(request, 'base/change_password.html')


# ── Gerenciamento de Usuários (admin only) ────────────────────────────────────

def _admin_required(request):
    return request.user.is_authenticated and request.user.role == 'admin'


@login_required
def user_list(request):
    if not _admin_required(request):
        return redirect('dashboard')
    users = User.objects.select_related('company').order_by('first_name', 'username')
    return render(request, 'admin/users.html', {'users': users})


@login_required
def user_create(request):
    if not _admin_required(request):
        return redirect('dashboard')
    companies = Company.objects.filter(is_active=True).order_by('name')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        role = request.POST.get('role', 'client')
        company_id = request.POST.get('company') or None
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '').strip()

        if not username or not email or not password:
            messages.error(request, 'Usuário, e-mail e senha temporária são obrigatórios.')
            return render(request, 'admin/user_form.html', {'companies': companies})

        if User.objects.filter(username=username).exists():
            messages.error(request, f'O usuário "{username}" já existe.')
            return render(request, 'admin/user_form.html', {'companies': companies})

        user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=role,
            phone=phone,
            must_change_password=True,
        )
        if company_id:
            user.company_id = company_id
        user.set_password(password)
        user.save()
        messages.success(request, f'Usuário {user.get_full_name() or username} criado. Na próximo login ele deverá trocar a senha.')
        return redirect('user_list')

    return render(request, 'admin/user_form.html', {'companies': companies})


@login_required
def user_edit(request, pk):
    if not _admin_required(request):
        return redirect('dashboard')
    u = get_object_or_404(User, pk=pk)
    companies = Company.objects.filter(is_active=True).order_by('name')
    if request.method == 'POST':
        u.first_name = request.POST.get('first_name', u.first_name)
        u.last_name = request.POST.get('last_name', u.last_name)
        u.email = request.POST.get('email', u.email)
        u.role = request.POST.get('role', u.role)
        u.phone = request.POST.get('phone', u.phone)
        company_id = request.POST.get('company') or None
        u.company_id = company_id

        new_password = request.POST.get('new_password', '').strip()
        if new_password:
            u.set_password(new_password)
            u.must_change_password = True

        u.save()
        messages.success(request, 'Usuário atualizado.')
        return redirect('user_list')

    return render(request, 'admin/user_form.html', {'companies': companies, 'edit_user': u})


@login_required
def user_toggle_active(request, pk):
    if not _admin_required(request):
        return redirect('dashboard')
    u = get_object_or_404(User, pk=pk)
    if u == request.user:
        messages.error(request, 'Você não pode desativar sua própria conta.')
        return redirect('user_list')
    u.is_active = not u.is_active
    u.save(update_fields=['is_active'])
    status = 'ativado' if u.is_active else 'desativado'
    messages.success(request, f'Usuário {u.get_full_name() or u.username} {status}.')
    return redirect('user_list')
