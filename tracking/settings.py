from django.conf import settings

TRACK_AJAX_REQUESTS = getattr(settings, 'TRACK_AJAX_REQUESTS', False)
TRACK_ANONYMOUS_USERS = getattr(settings, 'TRACK_ANONYMOUS_USERS', True)

TRACK_PAGEVIEWS = getattr(settings, 'TRACK_PAGEVIEWS', False)

TRACK_IGNORE_URLS = getattr(settings, 'TRACK_IGNORE_URLS', (
    r'^(favicon\.ico|robots\.txt)$',
))

TRACK_IGNORE_STATUS_CODES = getattr(settings, 'TRACK_IGNORE_STATUS_CODES', [])

TRACK_USING_GEOIP = getattr(settings, 'TRACK_USING_GEOIP', False)
if hasattr(settings, 'TRACKING_USE_GEOIP'):
    raise DeprecationWarning('TRACKING_USE_GEOIP is now TRACK_USING_GEOIP')

TRACK_REFERER = getattr(settings, 'TRACK_REFERER', False)

TRACK_QUERY_STRING = getattr(settings, 'TRACK_QUERY_STRING', False)
