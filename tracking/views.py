import logging
import calendar
from datetime import date, timedelta
from django.db.models import Min
from django.shortcuts import render
from django.contrib.auth.decorators import permission_required
from tracking.models import Visitor, Pageview
from tracking.settings import TRACK_PAGEVIEWS
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.core.paginator import Paginator, EmptyPage
from django.core.urlresolvers import reverse

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

    return render(request, 'tracking/dashboard.html', context)

class PageNav(object):
    def __init__(self, url='', strong=False, text=''):
        self.url = url
        self.strong = strong
        self.text = text

def url_nav(uid, pn):
    url = "%s?p=%d" % (reverse('tracking-user-detail', args=(uid,)), pn)
    return PageNav(url=url, text=pn)

def append_page_links(uid, page_nums, page_links):
    for pn in page_nums:
        page_links.append(url_nav(uid, pn))

def prepend_page_links(uid, page_nums, page_links):
    page_nums.reverse()
    for pn in page_nums:
        page_links.insert(0, url_nav(uid, pn))

END_PAGES = 2
SURROUND_PAGES = 3
PAGE_SIZE = 50

@permission_required('tracking.view_visitor')
def user_detail(request, uid):
    """
    Shows pageviews in reverse datetime for a particular user

    All pageviews are aggregrated in one big table and not broken down
    by visits.

    The paginator works in a similar way to that used in Django's
    admin app. This works by showing the first and last 2 page links,
    plus 3 page links either side of the current page.
    """

    user = get_object_or_404(User, pk=uid)
    pageviews = Pageview.objects.filter(visitor__user=user)
    pages = Paginator(pageviews, PAGE_SIZE)
    try:
        this_pn = int(request.GET['p'])
        this_pn = min(this_pn, pages.num_pages)
        this_pn = max(1, this_pn)
    except (ValueError, KeyError):
        this_pn = 1
    page = pages.page(this_pn)
    page_links = []
    if pages.num_pages > 1:
        # This page number (not a link)
        page_links.append(PageNav(strong=True, text=this_pn))
        # Links to 3 previous page numbers
        lower_limit = max(this_pn - SURROUND_PAGES, 1)
        r = range(lower_limit, this_pn)
        prepend_page_links(uid, r, page_links)
        # "..." chars going back to 1st links
        if lower_limit > END_PAGES + 1:
            page_links.insert(0, PageNav(text="..."))
        # Pages 1 and 2 links
        r = range(1, min(lower_limit, END_PAGES + 1))
        prepend_page_links(uid, r, page_links)
        # Links to next 3 pages
        upper_limit = min(pages.num_pages + 1, this_pn + SURROUND_PAGES + 1)
        r = range(this_pn + 1, upper_limit)
        append_page_links(uid, r, page_links)
        # "..." chars before final links
        if upper_limit < pages.num_pages - END_PAGES + 1:
            page_links.append(PageNav(text="..."))
        # Final 2 page links
        r = range(max(upper_limit, pages.num_pages - END_PAGES + 1),
                      pages.num_pages + 1)
        append_page_links(uid, r, page_links)

    if user.get_full_name():
        name = user.get_full_name()
    elif user.email:
        name = user.email
    else:
        name = str(user)

    context = {
        'user': user,
        'user_name': name,
        'pageviews': page,
        'page_links': page_links,
    }
    return render(request, 'tracking/user_detail.html', context)
