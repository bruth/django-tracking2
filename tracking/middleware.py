import re
import logging
import warnings

from django.db import IntegrityError
from django.utils import timezone
from django.utils.encoding import smart_text

from tracking.models import Visitor, Pageview
from tracking.utils import get_ip_address, total_seconds
from tracking.settings import (
    TRACK_AJAX_REQUESTS,
    TRACK_ANONYMOUS_USERS,
    TRACK_IGNORE_STATUS_CODES,
    TRACK_IGNORE_URLS,
    TRACK_PAGEVIEWS,
    TRACK_QUERY_STRING,
    TRACK_REFERER,
)

track_ignore_urls = [re.compile(x) for x in TRACK_IGNORE_URLS]

log = logging.getLogger(__file__)


class VisitorTrackingMiddleware(object):
    def _should_track(self, user, request, response):
        # Session framework not installed, nothing to see here..
        if not hasattr(request, 'session'):
            msg = ('VisitorTrackingMiddleware installed without'
                   'SessionMiddleware')
            warnings.warn(msg, RuntimeWarning)
            return False

        # Do not track AJAX requests
        if request.is_ajax() and not TRACK_AJAX_REQUESTS:
            return False

        # Do not track if HTTP HttpResponse status_code blacklisted
        if response.status_code in TRACK_IGNORE_STATUS_CODES:
            return False

        # Do not tracking anonymous users if set
        if user is None and not TRACK_ANONYMOUS_USERS:
            return False

        # Do not track ignored urls
        path = request.path_info.lstrip('/')
        for url in track_ignore_urls:
            if url.match(path):
                return False

        # everything says we should track this hit
        return True

    def _refresh_visitor(self, user, request, visit_time):
        # A Visitor row is unique by session_key
        session_key = request.session.session_key

        try:
            visitor = Visitor.objects.get(pk=session_key)
        except Visitor.DoesNotExist:
            # Log the ip address. Start time is managed via the field
            # `default` value
            ip_address = get_ip_address(request)
            visitor = Visitor(pk=session_key, ip_address=ip_address)

        # Update the user field if the visitor user is not set. This
        # implies authentication has occured on this request and now
        # the user is object exists. Check using `user_id` to prevent
        # a database hit.
        if user and not visitor.user_id:
            visitor.user_id = user.id

        # update some session expiration details
        visitor.expiry_age = request.session.get_expiry_age()
        visitor.expiry_time = request.session.get_expiry_date()

        # grab the latest User-Agent and store it
        user_agent = request.META.get('HTTP_USER_AGENT', None)
        if user_agent:
            visitor.user_agent = smart_text(
                user_agent, encoding='latin-1', errors='ignore')

        time_on_site = 0
        if visitor.start_time:
            time_on_site = total_seconds(visit_time - visitor.start_time)
        visitor.time_on_site = int(time_on_site)

        try:
            visitor.save()
        except IntegrityError:
            # there is a small chance a second response has saved this
            # Visitor already and a second save() at the same time (having
            # failed to UPDATE anything) will attempt to INSERT the same
            # session key (pk) again causing an IntegrityError
            # If this happens we'll just grab the "winner" and use that!
            visitor = Visitor.objects.get(pk=session_key)

        return visitor

    def _add_pageview(self, visitor, request, view_time):
        referer = None
        query_string = None

        if TRACK_REFERER:
            referer = request.META.get('HTTP_REFERER', None)

        if TRACK_QUERY_STRING:
            query_string = request.META.get('QUERY_STRING')

        pageview = Pageview(
            visitor=visitor, url=request.path, view_time=view_time,
            method=request.method, referer=referer,
            query_string=query_string)
        pageview.save()

    def process_response(self, request, response):
        # If dealing with a non-authenticated user, we still should track the
        # session since if authentication happens, the `session_key` carries
        # over, thus having a more accurate start time of session
        user = getattr(request, 'user', None)
        if user and user.is_anonymous():
            # set AnonymousUsers to None for simplicity
            user = None

        # make sure this is a response we want to track
        if not self._should_track(user, request, response):
            return response

        # Force a save to generate a session key if one does not exist
        if not request.session.session_key:
            request.session.save()

        # Be conservative with the determining time on site since simply
        # increasing the session timeout could greatly skew results. This
        # is the only time we can guarantee.
        now = timezone.now()

        # update/create the visitor object for this request
        visitor = self._refresh_visitor(user, request, now)

        if TRACK_PAGEVIEWS:
            self._add_pageview(visitor, request, now)

        return response
