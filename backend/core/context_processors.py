from apps.notifications.models import Notification


def notifications_ctx(request):
    if request.user.is_authenticated:
        unread = Notification.objects.filter(user=request.user, read=False)
        return {
            'unread_notifications_count': unread.count(),
            'notifications': unread[:8],
        }
    return {}
