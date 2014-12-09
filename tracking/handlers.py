from django.utils import timezone
from django.core.cache import cache
from django.conf import settings
from tracking.models import Visitor
from tracking.cache import instance_cache_key

SESSION_COOKIE_AGE = getattr(settings, 'SESSION_COOKIE_AGE')


def track_ended_session(sender, request, user, **kwargs):
    try:
        visitor = Visitor.objects.get(pk=request.session.session_key)
    # This should rarely ever occur.. e.g. direct request to logout
    except Visitor.DoesNotExist:
        return

    # Explicitly end this session. This improves the accuracy of the stats.
    visitor.end_time = timezone.now()
    visitor.time_on_site = (visitor.end_time - visitor.start_time).seconds
    visitor.save()

    # Unset the cache since the user logged out, this particular visitor will
    # unlikely be accessed individually.
    cache.delete(instance_cache_key(visitor))


def post_save_cache(sender, instance, **kwargs):
    cache.set(instance_cache_key(instance), instance, SESSION_COOKIE_AGE)
