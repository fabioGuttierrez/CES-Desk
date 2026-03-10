from django.shortcuts import redirect

EXEMPT_URLS = {'/auth/trocar-senha/', '/auth/logout/'}


class ForcePasswordChangeMiddleware:
    """Redireciona usuários com must_change_password=True para trocar a senha."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            request.user.is_authenticated
            and getattr(request.user, 'must_change_password', False)
            and request.path not in EXEMPT_URLS
            and not request.path.startswith('/static/')
            and not request.path.startswith('/media/')
        ):
            return redirect('forced_password_change')
        return self.get_response(request)


class AuditMiddleware:
    """Middleware que registra IP e user-agent nas ações."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response
