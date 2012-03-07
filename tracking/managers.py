from datetime import date, datetime, timedelta
from django.db import models
from django.db.models import Count, Avg, Min, Max
from django.contrib.auth.models import User

def adjusted_date_range(start=None, end=None):
    today = date.today()
    if end:
        end = min(end, today) + timedelta(days=1)
    else:
        end = today
    return start, end

class VisitorManager(models.Manager):
    def active(self, registered_only=True):
        "Returns all active users, e.g. not logged and non-expired session."
        visitors = self.get_query_set().filter(expiry_time__gt=datetime.now(),
            end_time=None)
        if registered_only:
            visitors = visitors.filter(user__isnull=False)
        return visitors

    def registered(self):
        return self.get_query_set().filter(user__isnull=False)

    def guests(self):
        return self.get_query_set().filter(user__isnull=True)

    def tracked_dates(self):
        "Returns a date range of when tracking has occured."
        dates = self.get_query_set().aggregate(start_min=Min('start_time'),
            start_max=Max('start_time'))
        if dates:
            return [dates['start_min'].date, dates['start_max'].date]
        return []

    def stats(self, start_date=None, end_date=None, registered_only=False):
        """Returns a dictionary of visits including:

            * total visits
            * unique visits
            * return ratio

        for all users, registered users and guests.
        """
        start_date, end_date = adjusted_date_range(start_date, end_date)

        kwargs = {
            'start_time__lt': end_date,
        }
        if start_date:
            kwargs['start_time__gte'] = start_date

        visit_stats = {
            'total': 0,
            'unique': 0,
            'return_ratio': 0,
            'registered': {
                'total': 0,
                'unique': 0,
                'return_ratio': 0,
            },
            'guests': {
                'total': 0,
                'unique': 0,
                'return_ratio': 0,
            }
        }

        visitors = self.get_query_set().filter(**kwargs)
        visit_stats['total'] = total_visits = visitors.count()

        if not total_visits:
            return visit_stats

        # Registered user sessions
        registered_visitors = visitors.filter(user__isnull=False)
        registered_visits = registered_visitors.count()

        if registered_visits:
            unique_registered_visits = registered_visitors.values('user').distinct().count()
            visit_stats['unique'] += unique_registered_visits

            visit_stats['registered'] = {
                'total': registered_visits,
                'unique': unique_registered_visits,
                'return_ratio': float(registered_visits - unique_registered_visits) / registered_visits * 100
            }

        if not registered_only:
            guest_visitors = visitors.filter(user__isnull=True).values('ip_address', 'user_agent')
            guest_visits = guest_visitors.count()

            if guest_visits:
                unique_guest_visits = guest_visitors.distinct().count()
                visit_stats['unique'] += unique_guest_visits

                visit_stats['guests'] = {
                    'total': guest_visits,
                    'unique': unique_guest_visits,
                    'return_ratio': float(guest_visits - unique_guest_visits) / guest_visits * 100,
                }

        visit_stats['return_ratio'] = float(visit_stats['unique'] - visit_stats['total']) / visit_stats['total'] * 100

        from tracking.models import TRACK_PAGEVIEWS
        if TRACK_PAGEVIEWS:
            visit_stats['pages_per_visit'] = visitors.annotate(page_count=Count('pageviews'))\
                .aggregate(avg_pages=Avg('page_count'))['avg_pages']
            visit_stats['registered']['pages_per_visit'] = registered_visitors\
                .annotate(page_count=Count('pageviews')).aggregate(avg_pages=Avg('page_count'))['avg_pages']
            if not registered_only:
                visit_stats['guests']['pages_per_visit'] = guest_visitors\
                    .annotate(page_count=Count('pageviews')).aggregate(avg_pages=Avg('page_count'))['avg_pages']

        return visit_stats

    def user_stats(self, start_date=None, end_date=None):
        start_date, end_date = adjusted_date_range(start_date, end_date)
        kwargs = {
            'visit_history__start_time__lt': end_date,
        }
        if start_date:
            kwargs['visit_history__start_time__gte'] = start_date
        else:
            kwargs['visit_history__start_time__isnull'] = False

        return User.objects.filter(**kwargs).annotate(visit_count=Count('visit_history'),
            time_on_site_avg=Avg('visit_history__time_on_site'))


class PageviewManager(models.Manager):
    def stats(self, start_date=None, end_date=None, registered_only=False):
        """Returns a dictionary of pageviews including:

            * total pageviews
            * pages per visit

        for all users, registered users and guests.
        """
        start_date, end_date = adjusted_date_range(start_date, end_date)

        kwargs = {
            'visitor__start_time__lt': end_date,
        }
        if start_date:
            kwargs['visitor__start_time__gte'] = start_date

        pageview_stats = {
            'total': 0,
            'unique': 0,
            'registered': {
                'total': 0,
                'unique': 0,
            },
            'guests': {
                'total': 0,
                'unique': 0,
            }
        }

        pageviews = self.get_query_set().filter(**kwargs)
        pageview_stats['total'] = total_views = pageviews.count()

        if not total_views:
            return pageview_stats

        # Registered user sessions
        registered_pageviews = pageviews.filter(visitor__user__isnull=False)
        registered_pageview_count = registered_pageviews.count()

        if registered_pageview_count:
            unique_registered_pageview_count = registered_pageviews.values('visitor__user').distinct().count()
            pageview_stats['unique'] += unique_registered_pageview_count

            pageview_stats['registered'] = {
                'total': registered_pageview_count,
                'unique': unique_registered_pageview_count,
            }

        if not registered_only:
            guest_pageviews = pageviews.filter(user__isnull=True).values('ip_address', 'user_agent')
            guest_pageview_count = guest_pageviews.count()

            if guest_pageview_count:
                unique_guest_pageview_count = guest_pageviews.distinct().count()
                pageview_stats['unique'] += unique_guest_pageview_count

                pageview_stats['guests'] = {
                    'total': guest_pageview_count,
                    'unique': unique_guest_pageview_count,
                }

        return pageview_stats

