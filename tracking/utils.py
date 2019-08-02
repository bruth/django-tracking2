from __future__ import division

from datetime import timedelta

from django import forms
from django.utils.timezone import now
from django.core.exceptions import ValidationError
from django.core.validators import validate_ipv46_address

from tracking.models import Visitor

headers = (
    'HTTP_CLIENT_IP', 'HTTP_X_FORWARDED_FOR', 'HTTP_X_FORWARDED',
    'HTTP_X_CLUSTERED_CLIENT_IP', 'HTTP_FORWARDED_FOR', 'HTTP_FORWARDED',
    'REMOTE_ADDR'
)

# tracking wants to accept more formats than default, here they are
input_formats = [
    '%Y-%m-%d %H:%M:%S',    # '2006-10-25 14:30:59'
    '%Y-%m-%d %H:%M',       # '2006-10-25 14:30'
    '%Y-%m-%d',             # '2006-10-25'
    '%Y-%m',                # '2006-10'
    '%Y',                   # '2006'
]


class TimeRangeForm(forms.Form):
    start = forms.DateTimeField(required=False, input_formats=input_formats)
    end = forms.DateTimeField(required=False, input_formats=input_formats)

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

def processTimeRangeForm(request):
    end_time = now()
    start_time = end_time - timedelta(days=7)
    defaults = {'start': start_time, 'end': end_time}
    form = TimeRangeForm(data=(request.GET if 'end' in request.GET else None) or defaults)
    if form.is_valid():
        start_time = form.cleaned_data['start']
        end_time = form.cleaned_data['end']
    # determine when tracking began
    try:
        obj = Visitor.objects.order_by('start_time')[0]
        track_start_time = obj.start_time
    except (IndexError, Visitor.DoesNotExist):
        track_start_time = now()
    # If the start_date is before tracking began, warn about incomplete data
    warn_incomplete = (start_time < track_start_time)
    return (start_time, end_time, track_start_time, warn_incomplete, form)