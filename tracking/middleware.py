import re
import logging
from datetime import datetime
from django.utils import timezone
from tracking.models import Visitor, Pageview
from tracking.utils import get_ip_address
from tracking.settings import (TRACK_AJAX_REQUESTS,
    TRACK_ANONYMOUS_USERS, TRACK_PAGEVIEWS, TRACK_IGNORE_URLS, TRACK_IGNORE_STATUS_CODES, TRACK_REFERER, TRACK_QUERY_STRING)

TRACK_IGNORE_URLS = [re.compile(x) for x in TRACK_IGNORE_URLS]

log = logging.getLogger(__file__)
pattern = "(up.browser|up.link|mmp|symbian|smartphone|midp|wap|phone|windows ce|pda|mobile|mini|palm|netfront|mobi|avantgo|bolt|android|ipad|pock
et|lynx|links|tablet|armv5|armv6|armv7)"
prog = re.compile(pattern, re.IGNORECASE)
wap_pattern = "application/vnd\.wap\.xhtml\+xml"
wap_prog = re.compile(pattern, re.IGNORECASE)

class VisitorTrackingMiddleware(object):
    def is_mobile_bowser(self, request):
        """
        Method to detect if the request is from a mobile browser or not.
        """
        is_mobile = False
        if request.META.has_key('HTTP_USER_AGENT'):
            user_agent = request.META['HTTP_USER_AGENT']
            match = prog.search(user_agent)
            if match:
                is_mobile = True
            else:
                if 'HTTP_ACCEPT' in request.META:
                    http_accept = request.META['HTTP_ACCEPT']
                    match = wap_prog.search(http_accept)
                    if match:
                        is_mobile = True
            if not is_mobile:
                # Now we test the user_agent from a big list.
                user_agents_test = ("w3c ", "acs-", "alav", "alca", "amoi", "audi",
                                    "avan", "benq", "bird", "blac", "blaz", "brew",
                                    "cell", "cldc", "cmd-", "dang", "doco", "eric",
                                    "hipt", "inno", "ipaq", "java", "jigs", "kddi",
                                    "keji", "leno", "lg-c", "lg-d", "lg-g", "lge-",
                                    "maui", "maxo", "midp", "mits", "mmef", "mobi",
                                    "mot-", "moto", "mwbp", "nec-", "newt", "noki",
                                    "xda",  "palm", "pana", "pant", "phil", "play",
                                    "port", "prox", "qwap", "sage", "sams", "sany",
                                    "sch-", "sec-", "send", "seri", "sgh-", "shar",
                                    "sie-", "siem", "smal", "smar", "sony", "sph-",
                                    "symb", "t-mo", "teli", "tim-", "tosh", "tsm-",
                                    "upg1", "upsi", "vk-v", "voda", "wap-", "wapa",
                                    "wapi", "wapp", "wapr", "webc", "winw", "winw",
                                    "xda-","htc_")

                test = user_agent[0:4].lower()
                if test in user_agents_test:
                    is_mobile = True
        return is_mobile
    def process_response(self, request, response):
        # Session framework not installed, nothing to see here..
        if not hasattr(request, 'session'):
            return response

        # Do not track AJAX requests..
        if request.is_ajax() and not TRACK_AJAX_REQUESTS:
            return response

        # Do not track if HTTP HttpResponse status_code blacklisted
        if response.status_code in TRACK_IGNORE_STATUS_CODES:
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

        # Force a save to generate a session key if one does not exist
        if not request.session.session_key:
            request.session.save()

        # A Visitor row is unique by session_key
        session_key = request.session.session_key

        try:
            visitor = Visitor.objects.get(pk=session_key)
        except Visitor.DoesNotExist:
            # Log the ip address. Start time is managed via the
            # field `default` value
            visitor = Visitor(pk=session_key, ip_address=get_ip_address(request),
                user_agent=request.META.get('HTTP_USER_AGENT', None), is_mobile=self.is_mobile_bowser(request))

        # Update the user field if the visitor user is not set. This
        # implies authentication has occured on this request and now
        # the user is object exists. Check using `user_id` to prevent
        # a database hit.
        if user and not visitor.user_id:
            visitor.user = user

        visitor.expiry_age = request.session.get_expiry_age()
        visitor.expiry_time = request.session.get_expiry_date()

        # Be conservative with the determining time on site since simply
        # increasing the session timeout could greatly skew results. This
        # is the only time we can guarantee.
        now = timezone.now()
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
                referer = None
                query_string = None

                if TRACK_REFERER:
                    referer = request.META.get('HTTP_REFERER', None)

                if TRACK_QUERY_STRING:
                    query_string = request.META.get('QUERY_STRING')

                pageview = Pageview(visitor=visitor, url=request.path,
                    view_time=now, method=request.method, referer=referer, query_string=query_string)
                pageview.save()

        return response
