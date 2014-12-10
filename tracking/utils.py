from __future__ import division

import socket

headers = (
    'HTTP_CLIENT_IP', 'HTTP_X_FORWARDED_FOR', 'HTTP_X_FORWARDED',
    'HTTP_X_CLUSTERED_CLIENT_IP', 'HTTP_FORWARDED_FOR', 'HTTP_FORWARDED',
    'REMOTE_ADDR'
)


def is_valid_ip_address(address_family, ip_str):
    try:
        socket.inet_pton(address_family, ip_str)
    except socket.error:
        return False
    else:
        return True


def _is_valid_ipv4_address(ip_str):
    return is_valid_ip_address(socket.AF_INET, ip_str)


def _is_valid_ipv6_address(ip_str):
    if ':' not in ip_str:
        return False
    return is_valid_ip_address(socket.AF_INET6, ip_str)


def get_ip_address(request):
    for header in headers:
        if request.META.get(header, None):
            ip = request.META[header].split(',')[0]
            if _is_valid_ipv6_address(ip) or _is_valid_ipv4_address(ip):
                return ip


def total_seconds(delta):
    day_seconds = (delta.days * 24 * 3600) + delta.seconds
    return (delta.microseconds + day_seconds * 10**6) / 10**6
