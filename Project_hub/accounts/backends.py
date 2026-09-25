from django.contrib.auth.backends import ModelBackend

from .models import User


class UsernameOrEmailBackend(ModelBackend):
    """Lets people sign in with either their username or their email."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username and "@" in username:
            user = User.objects.filter(email__iexact=username).first()
            if user:
                username = user.username
        return super().authenticate(request, username=username, password=password, **kwargs)
