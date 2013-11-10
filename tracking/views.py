import logging
import calendar
from warnings import warn
from datetime import datetime, time
from datetime import date, timedelta
from django.db.models import Min
from django.shortcuts import render
from django.contrib.auth.decorators import permission_required
from django.utils.timezone import now
from tracking.models import Visitor, Pageview
from tracking.settings import TRACK_PAGEVIEWS
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.core.paginator import Paginator, EmptyPage
from django.core.urlresolvers import reverse
from django.views.generic import ListView

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
def dashboard(request):
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

    user_stats = list(Visitor.objects.user_stats(start_date, end_date))

    track_start_time = Visitor.objects.order_by('start_time')[0].start_time
    # If the start_date is later than when tracking began, no reason
    # to warn about missing data
    if start_date and calendar.timegm(start_date.timetuple()) < calendar.timegm(track_start_time.timetuple()):
        warn_start_time = track_start_time
    else:
        warn_start_time = None
    context = {
        'errors': errors,
        'track_start_time': track_start_time,
        'warn_start_time': warn_start_time,
        'visitor_stats': Visitor.objects.stats(start_date, end_date),
        'user_stats': user_stats,
        'tracked_dates': Visitor.objects.tracked_dates(),
    }

    if TRACK_PAGEVIEWS:
        context['pageview_stats'] = Pageview.objects.stats(start_date, end_date)
    if not end_date:
        context['end_date'] = now()
    else:
        context['end_date'] = end_date
    if not start_date:
        context['start_date'] = track_start_time
    else:
        context['start_date'] = datetime.combine(start_date, time.min)

    return render(request, 'tracking/dashboard.html', context)

def stats(*args, **kwargs):
    warn('The stats view has been renamed to dashboard and the /dashboard/ URL has be moved to the root /', DeprecationWarning)
    return dashboard(*args, **kwargs)

class PageLinksMixin(object):

    END_PAGES = 2
    SURROUND_PAGES = 3
    paginate_by = 20
    page_kwarg = 'p'
    model_name_plural = None

    class PageNav(object):
        def __init__(self, url='', strong=False, text=''):
            self.url = url
            self.strong = strong
            self.text = text
        def __repr__(self):
            return "Text: %s\tBold: %s\tURL: %s" % (self.text, self.strong,
                                                    self.url)

    def url_nav(self, pn):
        return self.PageNav(url=self.page_url(pn), text=pn)

    def append_page_links(self, page_nums):
        for pn in page_nums:
            self.page_links.append(self.url_nav(pn))

    def prepend_page_links(self, page_nums):
        page_nums.reverse()
        for pn in page_nums:
            self.page_links.insert(0, self.url_nav(pn))

    def get_context_data(self, **kwargs):
        ctx = super(ListView, self).get_context_data(**kwargs)

        if ctx['is_paginated']:
            # This page number (not a link)
            this_pn = ctx['page_obj'].number
            self.page_links = [self.PageNav(strong=True, text=this_pn)]
            # Links to 3 previous page numbers
            lower_limit = max(this_pn - self.SURROUND_PAGES, 1)
            self.prepend_page_links(range(lower_limit, this_pn))
            # "..." chars going back to 1st links
            if lower_limit > self.END_PAGES + 1:
                self.page_links.insert(0, self.PageNav(text="..."))
            # Pages 1 and 2 links
            self.prepend_page_links(range(1, min(lower_limit,
                                                 self.END_PAGES + 1)))
            # Links to next 3 pages
            num_pages = ctx['paginator'].num_pages
            upper_limit = min(num_pages + 1, this_pn + self.SURROUND_PAGES + 1)
            self.append_page_links(range(this_pn + 1, upper_limit))
            # "..." chars before final links
            if upper_limit < num_pages - self.END_PAGES + 1:
                self.page_links.append(self.PageNav(text="..."))
            # Final 2 page links
            r = range(max(upper_limit, num_pages - self.END_PAGES + 1),
                      num_pages + 1)
            self.append_page_links(r)
            ctx['page_links'] = self.page_links
            if self.model_name_plural:
                ctx['model_name_plural'] = self.model_name_plural
            else:
                ctx['model_name_plural'] = (
                    ctx['object_list'].model._meta.object_name.lower() + 's')

        return ctx

def add_username_to_context(user, ctx):
    if user.get_full_name():
        name = user.get_full_name()
    elif user.email:
        name = user.email
    else:
        name = str(user)
    ctx['user_name'] = name

class UserVisits(PageLinksMixin, ListView):

    template_name = "tracking/user_visits.html"
    model_name_plural = "visits"

    def page_url(self, pn):
        uid = self.user.pk
        return "%s?p=%d" % (reverse('tracking-user-visits', args=(uid,)), pn)

    def get_queryset(self):
        self.user = get_object_or_404(User, pk=self.args[0])
        return Visitor.objects.filter(user=self.user)

    def get_context_data(self, **kwargs):
        ctx = super(UserVisits, self).get_context_data(**kwargs)
        add_username_to_context(self.user, ctx)
        return ctx

class PageViews(PageLinksMixin, ListView):

    model_name_plural = "page views"

    def page_url(self, pn):
        pk = self.visitor.pk
        return "%s?p=%d" % (reverse('tracking-pageviews', args=(pk,)), pn)

    def get_queryset(self):
        self.visitor = get_object_or_404(Visitor, pk=self.args[0])
        return Pageview.objects.filter(visitor=self.visitor)

    def get_context_data(self, **kwargs):
        ctx = super(PageViews, self).get_context_data(**kwargs)
        ctx['visitor'] = self.visitor
        if self.visitor.user:
            add_username_to_context(self.visitor.user, ctx)
        return ctx
