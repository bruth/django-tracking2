import logging
import calendar

from datetime import timedelta

from django import forms
from django.shortcuts import render
from django.contrib.auth.decorators import permission_required
from django.utils.timezone import now

from tracking.models import Visitor, Pageview
from tracking.settings import TRACK_PAGEVIEWS

log = logging.getLogger(__file__)

# tracking wants to accept more formats than default, here they are
input_formats = [
    '%Y-%m-%d %H:%M:%S',    # '2006-10-25 14:30:59'
    '%Y-%m-%d %H:%M',       # '2006-10-25 14:30'
    '%Y-%m-%d',             # '2006-10-25'
    '%Y-%m',                # '2006-10'
    '%Y',                   # '2006'
]


class DashboardForm(forms.Form):
    start_time = forms.DateTimeField(
        required=False, input_formats=input_formats)
    end_time = forms.DateTimeField(
        required=False, input_formats=input_formats)


@permission_required('tracking.view_visitor')
def dashboard(request):
    "Counts, aggregations and more!"
    end_time = now()
    start_time = end_time - timedelta(days=1)
    defaults = {'start_time': start_time, 'end_time': end_time}

    form = DashboardForm(data=request.GET or defaults)
    if form.is_valid():
        start_time = form.cleaned_data['start_time']
        end_time = form.cleaned_data['end_time']

    user_stats = Visitor.objects.user_stats(
        start_time.date(), end_time.date())

    try:
        track_start_time = Visitor.objects.latest('start_time').start_time
    except Visitor.DoesNotExist:
        track_start_time = now()

    # If the start_date is later than when tracking began, no reason
    # to warn about missing data
    start_timestamp = calendar.timegm(start_time.timetuple())
    tracking_timestamp = calendar.timegm(track_start_time.timetuple())
    if start_timestamp < tracking_timestamp:
        warn_start_time = track_start_time
    else:
        warn_start_time = None
    context = {
        'form': form,
        'track_start_time': track_start_time,
        'warn_start_time': warn_start_time,
        'visitor_stats': Visitor.objects.stats(start_time.date(),
                                               end_time.date()),
        'user_stats': user_stats,
        'tracked_dates': Visitor.objects.tracked_dates(),
    }

    if TRACK_PAGEVIEWS:
        pageview_stats = Pageview.objects.stats(start_time, end_time)
        context['pageview_stats'] = pageview_stats

    context['start_date'] = track_start_time
    context['end_date'] = end_time

    return render(request, 'tracking/dashboard.html', context)
