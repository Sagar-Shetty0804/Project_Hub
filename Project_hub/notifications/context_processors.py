def notifications(request):
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {}
    qs = user.notifications.all()
    return {
        "unread_count": qs.filter(is_read=False).count(),
        "recent_notifications": qs[:6],
    }
