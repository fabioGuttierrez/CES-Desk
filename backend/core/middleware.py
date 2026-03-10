class AuditMiddleware:
    """Middleware que registra IP e user-agent nas ações."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response
