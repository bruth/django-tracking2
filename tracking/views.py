import logging

from datetime import timedelta
from statistics import mean
from functools import reduce
from operator import add

from django import forms
from django.shortcuts import (
    render,
    get_object_or_404,
)
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import permission_required
from django.utils.timezone import now
from django.db.models import Count, Avg, Sum

from tracking.models import Visitor, Pageview
from tracking.settings import TRACK_PAGEVIEWS
from _collections import OrderedDict

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
    start = forms.DateTimeField(required=False, input_formats=input_formats)
    end = forms.DateTimeField(required=False, input_formats=input_formats)


@permission_required('tracking.visitor_log')
def dashboard(request):
    "Counts, aggregations and more!"
    end_time = now()
    start_time = end_time - timedelta(days=7)
    defaults = {'start': start_time, 'end': end_time}

    form = DashboardForm(data=request.GET or defaults)
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

    # queries take `date` objects (for now)
    user_stats = Visitor.objects.user_stats(start_time, end_time)
    visitor_stats = Visitor.objects.stats(start_time, end_time)
    if TRACK_PAGEVIEWS:
        pageview_stats = Pageview.objects.stats(start_time, end_time)
    else:
        pageview_stats = None

    context = {
        'form': form,
        'track_start_time': track_start_time,
        'warn_incomplete': warn_incomplete,
        'user_stats': user_stats,
        'visitor_stats': visitor_stats,
        'pageview_stats': pageview_stats,
    }
    return render(request, 'tracking/dashboard.html', context)

@permission_required('tracking.visitor_log')
def visitor_overview(request, user_id):
    "Counts, aggregations and more!"
#     user = get_object_or_404(get_user_model(), pk=user_id)
    end_time = now()
    start_time = end_time - timedelta(days=7)
    defaults = {'start': start_time, 'end': end_time}

    form = DashboardForm(data=request.GET or defaults)
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

    # queries take `date` objects (for now)
    user = Visitor.objects.user_stats(start_time, end_time).filter(pk=user_id).first()
    visits = Visitor.objects.filter(user=user, start_time__range=(start_time, end_time))

    context = {
        'form': form,
        'track_start_time': track_start_time,
        'warn_incomplete': warn_incomplete,
        'visits': visits,
        'user': user,
    }
    return render(request, 'tracking/visitor_overview.html', context)

@permission_required('tracking.visitor_log')
def visitor_visits(request, visit_id):
    visit = get_object_or_404(Visitor, pk=visit_id)
    pageviews = visit.pageviews.all()
    pageview_stats = {}
    for v in pageviews:
        if v.url not in pageview_stats:
            pageview_stats[v.url] = 0
        pageview_stats[v.url] += 1
    pageview_stats = OrderedDict(sorted(pageview_stats.items(), key=lambda x: x[1], reverse=True))

    context = {
        'visit': visit,
        'pageviews': pageviews,
        'pageview_stats': pageview_stats,
    }
    return render(request, 'tracking/visitor_visits.html', context)

@permission_required('tracking.visitor_log')
def visitor_page_detail(request, user_id, page_url):
    user = get_object_or_404(get_user_model(), pk=user_id)
    pageviews = Pageview.objects.filter(url=page_url, visitor__user__pk=user_id)
    numPageViews = 0
    viewsPerVisit = {}
    for v in pageviews:
        numPageViews += 1
        if v.pk not in viewsPerVisit:
            viewsPerVisit[v.pk] = 0
        viewsPerVisit[v.pk] += 1
    visits = Visitor.objects.filter(pageviews__in=pageviews).distinct().order_by('end_time', 'start_time')

    context = {
        'total_views': numPageViews,
        'avg_views_per_visit': mean(viewsPerVisit.values()),
        'visits': visits,
        'user': user,
        'page_url': page_url,
    }
    return render(request, 'tracking/visitor_page_detail.html', context)

@permission_required('tracking.visitor_log')
def visitor_pageview_detail(request, user_id, pageview_id):
    pageview = get_object_or_404(Pageview, pk=pageview_id)

    context = {
        'pageview': pageview,
    }
    return render(request, 'tracking/visitor_pageview_detail.html', context)

@permission_required('tracking.visitor_log')
def page_overview(request):
    pageview_counts = Pageview.objects.values('url').annotate(views=Count('url')).order_by('-views')

    context = {
        'pageview_counts': pageview_counts,
        'total_page_views': reduce(lambda acc, c: acc + c['views'], pageview_counts, 0),
        'total_pages': len(pageview_counts),
    }
    return render(request, 'tracking/page_overview.html', context)
