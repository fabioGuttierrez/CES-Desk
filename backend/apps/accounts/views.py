from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages


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
