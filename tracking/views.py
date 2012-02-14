import logging
import calendar
from datetime import date, timedelta
from django.shortcuts import render
from django.contrib.auth.decorators import permission_required
from tracking.models import Visitor

log = logging.getLogger(__file__)

def parse_partial_date(date_str, upper=False):
    if not date_str:
        return

    day = None
    toks = [int(x) for x in date_str.split('-')]

    if len(toks) > 3:
        return None

    if len(toks) == 3:
        year, month, day = toks
    # Nissing day
    elif len(toks) == 2:
        year, month = toks
    # Only year
    elif len(toks) == 1:
        year, = toks
        month = 1 if upper else 12

    if not day:
        day = calendar.monthrange(year, month)[0] if upper else 1

    return date(year, month, day)


@permission_required('tracking.view_visitor')
def stats(request):
    "Counts, aggregations and more!"
    errors = []
    start_date, end_date = None, None

    try:
        start_str = request.GET.get('start', None)
        start_date = parse_partial_date(start_str)
    except (ValueError, TypeError):
        errors.append('<code>{0}</code> is not a valid start date'.format(start_str))

    try:
        end_str = request.GET.get('end', None)
        end_date = parse_partial_date(end_str, upper=True)
    except (ValueError, TypeError):
        errors.append('<code>{0}</code> is not a valid end date'.format(end_str))

    user_stats = list(Visitor.objects.user_stats(start_date, end_date).order_by('time_on_site_avg'))
    for user in user_stats:
        if user.time_on_site_avg is not None:
            # Lop off the floating point
            user.time_on_site_avg = timedelta(seconds=int(user.time_on_site_avg))

    return render(request, 'tracking/dashboard.html', {
        'errors': errors,
        'visitor_stats': Visitor.objects.stats(start_date, end_date),
        'user_stats': user_stats,
        'tracked_dates': Visitor.objects.tracked_dates(),
    })
