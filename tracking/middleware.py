import re
import logging
from datetime import datetime
from tracking.models import Visitor, Pageview
from tracking.utils import get_ip_address
from tracking.settings import (TRACK_AJAX_REQUESTS,
    TRACK_ANONYMOUS_USERS, TRACK_PAGEVIEWS, TRACK_IGNORE_URLS)

TRACK_IGNORE_URLS = map(lambda x: re.compile(x), TRACK_IGNORE_URLS)

log = logging.getLogger(__file__)

class VisitorTrackingMiddleware(object):
    def process_response(self, request, response):
        # Session framework not installed, nothing to see here..
        if not hasattr(request, 'session'):
            return response

        # Do not track AJAX requests..
        if request.is_ajax() and not TRACK_AJAX_REQUESTS:
            return response

        # If dealing with a non-authenticated user, we still should track the
        # session since if authentication happens, the `session_key` carries
        # over, thus having a more accurate start time of session
        user = getattr(request, 'user', None)

        # Check for anonymous users
        if not user or user.is_anonymous():
            if not TRACK_ANONYMOUS_USERS:
                return response
            user = None

        # A Visitor row is unique by session_key
        session_key = request.session.session_key

        try:
            visitor = Visitor.objects.get(pk=session_key)
            # Update the user field if the visitor user is not set. This
            # implies authentication has occured on this request and now
            # the user is object exists. Check using `user_id` to prevent
            # a database hit.
            if user and not visitor.user_id:
                visitor.user = user
        except Visitor.DoesNotExist:
            # Log the ip address. Start time is managed via the
            # field `default` value
            visitor = Visitor(pk=session_key, ip_address=get_ip_address(request),
                user_agent=request.META.get('HTTP_USER_AGENT', None))

        visitor.expiry_age = request.session.get_expiry_age()
        visitor.expiry_time = request.session.get_expiry_date()

        # Be conservative with the determining time on site since simply
        # increasing the session timeout could greatly skew results. This
        # is the only time we can guarantee.
        now = datetime.now()
        time_on_site = 0
        if visitor.start_time:
            time_on_site = (now - visitor.start_time).seconds
        visitor.time_on_site = time_on_site

        visitor.save()

        if TRACK_PAGEVIEWS:
            # Match against `path_info` to not include the SCRIPT_NAME..
            path = request.path_info.lstrip('/')
            for url in TRACK_IGNORE_URLS:
                if url.match(path):
                    break
            else:
                pageview = Pageview(visitor=visitor, url=request.path, view_time=now)
                pageview.save()

        return response
