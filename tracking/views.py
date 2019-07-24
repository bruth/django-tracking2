import logging

from _collections import OrderedDict
from datetime import timedelta
from statistics import mean
from functools import reduce
from operator import add

from django import forms
from django.shortcuts import (
    render,
    get_object_or_404,
)
from django.http import HttpResponseNotFound
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import permission_required
from django.utils.timezone import now
from django.db.models import Count, Avg, Sum
from django.core.paginator import Paginator

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
    for us in user_stats:
        us.time_on_site = timedelta(seconds=us.time_on_site)
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
    page = request.GET.get('page', 1)
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
    if user:
        user.time_on_site = timedelta(seconds=user.time_on_site)
    visits = Visitor.objects.filter(user=user, start_time__range=(start_time, end_time))
    paginator = Paginator(visits, 100)

    context = {
        'form': form,
        'track_start_time': track_start_time,
        'warn_incomplete': warn_incomplete,
        'visits': paginator.page(page),
        'user': user,
    }
    return render(request, 'tracking/visitor_overview.html', context)

@permission_required('tracking.visitor_log')
def visitor_visits(request, visit_id):
    pvpage = request.GET.get('pvpage', 1)
    pvspage = request.GET.get('pvspage', 1)
    visit = get_object_or_404(Visitor, pk=visit_id)
    visit.time_on_site = timedelta(seconds=visit.time_on_site)
    pvcount = visit.pageviews.count()
    pageviews = visit.pageviews.order_by('-view_time')
    pageview_stats = visit.pageviews.values('url').annotate(views=Count('url')).order_by('-views')
    pvspaginator = Paginator(pageview_stats, 100)
    pvpaginator = Paginator(pageviews, 100)

    context = {
        'visit': visit,
        'pageviews': pvpaginator.page(pvpage),
        'pageview_stats': pvspaginator.page(pvspage),
        'pvcount': pvcount,
        'avg_time_per_page': visit.time_on_site/pvcount if pvcount else None
    }
    return render(request, 'tracking/visitor_visits.html', context)

@permission_required('tracking.visitor_log')
def visitor_page_detail(request, user_id):
    try:
        page_url = request.GET['page_url']
    except:
        return HttpResponseNotFound()   

    end_time = now()
    start_time = end_time - timedelta(days=7)
    defaults = {'start': start_time, 'end': end_time}

    form = DashboardForm(data=(request.GET if 'end' in request.GET else None) or defaults)
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

    page = request.GET.get('page', 1)
    user = get_object_or_404(get_user_model(), pk=user_id)
    relevant_visits = Visitor.objects.filter(
        pageviews__url=page_url,
        user__pk=user_id,
        start_time__lt=end_time,
    )
    if start_time:
        relevant_visits = relevant_visits.filter(start_time__gte=start_time)
    else:
        relevant_visits = relevant_visits.filter(start_time__isnull=False)
    
    aggs = relevant_visits.values('pk').annotate(views=Count('pageviews')).aggregate(
        Avg('views'),
        Sum('views')
    )
    visits = relevant_visits.distinct().order_by(
        'end_time',
        'start_time'
    )
    paginator = Paginator(visits, 100)

    context = {
        'total_views': aggs['views__sum'],
        'avg_views_per_visit': aggs['views__avg'],
        'visits': paginator.page(page),
        'user': user,
        'page_url': page_url,
        'form': form,
        'track_start_time': track_start_time,
        'warn_incomplete': warn_incomplete,
    }
    return render(request, 'tracking/visitor_page_detail.html', context)

@permission_required('tracking.visitor_log')
def visitor_pageview_detail(request, user_id, pageview_id):
    pageview = get_object_or_404(Pageview, pk=pageview_id, visitor__user_id=user_id)
    next_pv = Pageview.objects.filter(
        visitor__user_id=user_id,
        view_time__gt=pageview.view_time,
    ).order_by('view_time').first()
    if next_pv:
        duration = next_pv.view_time - pageview.view_time
    else:
        duration = None

    context = {
        'pageview': pageview,
        'duration': duration,
    }
    return render(request, 'tracking/visitor_pageview_detail.html', context)

@permission_required('tracking.visitor_log')
def page_overview(request):
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

    page = request.GET.get('page', 1)
    relevant_pvs = Pageview.objects.filter(view_time__lt=end_time)
    if start_time:
        relevant_pvs = relevant_pvs.filter(view_time__gte=start_time)
    pageview_counts = relevant_pvs.values('url').annotate(views=Count('url')).order_by('-views')
    paginator = Paginator(pageview_counts, 100)

    context = {
        'pageview_counts': paginator.page(page),
        'total_page_views': reduce(lambda acc, c: acc + c['views'], pageview_counts, 0),
        'total_pages': len(pageview_counts),
        'form': form,
        'track_start_time': track_start_time,
        'warn_incomplete': warn_incomplete,
    }
    return render(request, 'tracking/page_overview.html', context)

@permission_required('tracking.visitor_log')
def page_detail(request):
    try:
        page_url = request.GET['page_url']
    except:
        return HttpResponseNotFound()   

    end_time = now()
    start_time = end_time - timedelta(days=7)
    defaults = {'start': start_time, 'end': end_time}

    form = DashboardForm(data=(request.GET if 'end' in request.GET else None) or defaults)
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

    page = request.GET.get('page', 1)
    relevant_pvs = Pageview.objects.filter(view_time__lt=end_time)
    if start_time:
        relevant_pvs = relevant_pvs.filter(view_time__gte=start_time)
    pageviews = relevant_pvs.filter(url=page_url).order_by('-view_time')
    pv_count = pageviews.count()
    uniqueVisitors = relevant_pvs.values('visitor_id').distinct().count()
    paginator = Paginator(pageviews, 100)

    context = {
        'total_views': pv_count,
        'visitors': uniqueVisitors,
        'pageviews': paginator.page(page),
        'page_url': page_url,
        'form': form,
        'track_start_time': track_start_time,
        'warn_incomplete': warn_incomplete,
    }
    return render(request, 'tracking/page_detail.html', context)
