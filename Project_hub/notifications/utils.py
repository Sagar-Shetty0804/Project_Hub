import logging

from django.conf import settings
from django.core.mail import send_mail

from .models import Notification

log = logging.getLogger(__name__)


def notify(recipients, text, url="", actor=None, email=False):
    """Create an in-app notification for each recipient (skipping the actor).

    If `email` is true and EMAIL_NOTIFICATIONS is enabled, also send a short email.
    Email failures are logged, never raised, so they can't break the request.
    """
    recipients = {r for r in recipients if r is not None and r != actor}
    Notification.objects.bulk_create(
        [Notification(recipient=r, actor=actor, text=text, url=url) for r in recipients]
    )
    if email and settings.EMAIL_NOTIFICATIONS:
        addresses = [r.email for r in recipients if r.email]
        if addresses:
            try:
                send_mail(f"ProjectHub: {text[:70]}", f"{text}\n\nOpen ProjectHub to see more.",
                          settings.DEFAULT_FROM_EMAIL, addresses)
            except Exception:  # noqa: BLE001 - email is best-effort
                log.exception("Failed to send notification email")
