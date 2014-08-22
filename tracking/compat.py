# Django 1.7 support, falls back to get_user_model or
# auth.User to transparently work with <1.7
try:
    from django.apps import apps
    from django.conf import settings

    user_app, user_model = settings.AUTH_USER_MODEL.split('.')

    User = apps.get_app_config(user_app).get_model(user_model)
except ImportError:
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
    except ImportError:
        from django.contrib.auth.models import User