import logging
from datetime import datetime
from django.conf import settings
from tracking.models import Visitor
from tracking.utils import get_ip_address

TRACK_AJAX_REQUESTS = getattr(settings, 'TRACK_AJAX_REQUESTS', False)

log = logging.getLogger(__file__)

class VisitorTrackingMiddleware(object):
    def process_response(self, request, response):
        if not hasattr(request, 'session'):
            return response

        # Do not track AJAX requests..
        if request.is_ajax() and not TRACK_AJAX_REQUESTS:
            return response

        # If dealing with a non-authenticated user, we still should track the
        # session since if authentication happens, the `session_key` carries
        # over, thus having a more accurate start time of session

        user = getattr(request, 'user', None)
        # We cannot do anything with Anonymous users
        if user and not user.is_authenticated():
            user = None

        # A Visitor row is unique by session_key
        session_key = request.session.session_key

        try:
            visitor = Visitor.objects.get(session_key=session_key)
            # Update the user field if the visitor user is not set. This
            # implies authentication has occured on this request and now
            # the user is object exists. Check using `user_id` to prevent
            # a database hit.
            if user and not visitor.user_id:
                visitor.user = user
        except Visitor.DoesNotExist:
            # Log the ip address. Start time is managed via the
            # field `default` value
            visitor = Visitor(session_key=session_key,
                ip_address=get_ip_address(request),
                user_agent=request.META['HTTP_USER_AGENT'])

        visitor.expiry_age = request.session.get_expiry_age()
        visitor.expiry_time = request.session.get_expiry_date()

        # Be conservative with the determining time on site since simply
        # increasing the session timeout could greatly skew results. This
        # is the only time we can guarantee.
        time_on_site = 0
        if visitor.start_time:
            time_on_site = (datetime.now() - visitor.start_time).seconds
        visitor.time_on_site = time_on_site

        visitor.save()

        return response
