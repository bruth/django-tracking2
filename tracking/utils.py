from __future__ import division

from django.core.exceptions import ValidationError
from django.core.validators import validate_ipv46_address

headers = (
    'HTTP_CLIENT_IP', 'HTTP_X_FORWARDED_FOR', 'HTTP_X_FORWARDED',
    'HTTP_X_CLUSTERED_CLIENT_IP', 'HTTP_FORWARDED_FOR', 'HTTP_FORWARDED',
    'REMOTE_ADDR'
)


def get_ip_address(request):
    for header in headers:
        if request.META.get(header, None):
            ip = request.META[header].split(',')[0]

            try:
                validate_ipv46_address(ip)
                return ip
            except ValidationError:
                pass


def total_seconds(delta):
    day_seconds = (delta.days * 24 * 3600) + delta.seconds
    return (delta.microseconds + day_seconds * 10**6) / 10**6
