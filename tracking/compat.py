# Django 1.5 support, falls back to auth.User to transparently
# work with <1.5
try:
    from django.contrib.auth import get_user_model
    User = get_user_model()
except ImportError:
    from django.contrib.auth.models import User
