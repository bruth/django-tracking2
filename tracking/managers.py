from datetime import date, datetime, timedelta
from django.db import models
from django.db.models import Count, Avg, Min, Max
from django.contrib.auth.models import User
from tracking.settings import TRACK_PAGEVIEWS, TRACK_ANONYMOUS_USERS

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
        visitors = self.get_query_set().filter(expiry_time__gt=datetime.now(), end_time=None)
        if registered_only:
            visitors = visitors.filter(user__isnull=False)
        return visitors

    def registered(self):
        return self.get_query_set().filter(user__isnull=False)

    def guests(self):
        return self.get_query_set().filter(user__isnull=True)

    def tracked_dates(self):
        "Returns a date range of when tracking has occured."
        dates = self.get_query_set().aggregate(start_min=Min('start_time'), start_max=Max('start_time'))
        if dates:
            return [dates['start_min'].date(), dates['start_max'].date()]
        return []

    def stats(self, start_date=None, end_date=None, registered_only=False):
        """Returns a dictionary of visits including:

            * total visits
            * unique visits
            * return ratio
            * pages per visit (if pageviews are enabled)

        for all users, registered users and guests.
        """
        start_date, end_date = adjusted_date_range(start_date, end_date)

        kwargs = {'start_time__lt': end_date}
        if start_date:
            kwargs['start_time__gte'] = start_date

        stats = {
            'total': 0,
            'unique': 0,
            'return_ratio': 0,
        }

        # All visitors
        visitors = self.get_query_set().filter(**kwargs)
        stats['total'] = total_count = visitors.count()
        unique_count = 0

        # No visitors! Nothing more to do.
        if not total_count:
            return stats

        # Registered user sessions
        registered_visitors = visitors.filter(user__isnull=False)
        registered_total_count = registered_visitors.count()

        if registered_total_count:
            registered_unique_count = registered_visitors.values('user').distinct().count()

            # Update the total unique count..
            unique_count += registered_unique_count

            # Set the registered stats..
            stats['registered'] = {
                'total': registered_total_count,
                'unique': registered_unique_count,
                'return_ratio': float(registered_total_count - registered_unique_count) / registered_total_count * 100
            }

        # Get stats for our guests..
        if TRACK_ANONYMOUS_USERS and not registered_only:
            guest_visitors = visitors.filter(user__isnull=True)
            guest_total_count = guest_visitors.count()

            if guest_total_count:
                guest_unique_count = guest_visitors.values('ip_address').distinct().count()

                # Update the total unique count...
                unique_count += guest_unique_count

                stats['guests'] = {
                    'total': guest_total_count,
                    'unique': guest_unique_count,
                    'return_ratio': float(guest_total_count - guest_unique_count) / guest_total_count * 100,
                }

        # Finish setting the total visitor counts
        stats['unique'] = unique_count
        stats['return_ratio'] = float(total_count - unique_count) / total_count * 100

        # If pageviews are being tracked, add the aggregated pages-per-visit stat
        if TRACK_PAGEVIEWS:
            stats['registered']['pages_per_visit'] = registered_visitors\
                .annotate(page_count=Count('pageviews')).filter(page_count__gt=0)\
                .aggregate(pages_per_visit=Avg('page_count'))['pages_per_visit']

            if TRACK_ANONYMOUS_USERS and not registered_only:
                stats['guests']['pages_per_visit'] = guest_visitors\
                    .annotate(page_count=Count('pageviews')).filter(page_count__gt=0)\
                    .aggregate(pages_per_visit=Avg('page_count'))['pages_per_visit']

                total_per_visit = visitors.annotate(page_count=Count('pageviews'))\
                    .filter(page_count__gt=0).aggregate(pages_per_visit=Avg('page_count'))['pages_per_visit']
            else:
                total_per_visit = stats['registered']['pages_per_visit']

            stats['pages_per_visit'] = total_per_visit

        return stats

    def user_stats(self, start_date=None, end_date=None):
        start_date, end_date = adjusted_date_range(start_date, end_date)
        kwargs = {
            'visit_history__start_time__lt': end_date,
        }
        if start_date:
            kwargs['visit_history__start_time__gte'] = start_date
        else:
            kwargs['visit_history__start_time__isnull'] = False

        users = list(User.objects.annotate(
            visit_count=Count('visit_history'),
            time_on_site=Avg('visit_history__time_on_site'),
        ).filter(visit_count__gt=0).order_by('-time_on_site'))

        # Aggregate pageviews per visit
        for user in users:
            user.pages_per_visit = user.visit_history.annotate(page_count=Count('pageviews'))\
                .filter(page_count__gt=0).aggregate(pages_per_visit=Avg('page_count'))['pages_per_visit']
            # Lop off the floating point, turn into timedelta
            user.time_on_site = timedelta(seconds=int(user.time_on_site))
        return users


class PageviewManager(models.Manager):
    def stats(self, start_date=None, end_date=None, registered_only=False):
        """Returns a dictionary of pageviews including:

            * total pageviews

        for all users, registered users and guests.
        """
        start_date, end_date = adjusted_date_range(start_date, end_date)

        kwargs = {
            'visitor__start_time__lt': end_date,
        }
        if start_date:
            kwargs['visitor__start_time__gte'] = start_date

        stats = {
            'total': 0,
            'unique': 0,
        }

        pageviews = self.get_query_set().filter(**kwargs).select_related('visitor')
        stats['total'] = total_views = pageviews.count()
        unique_count = 0

        if not total_views:
            return stats

        # Registered user sessions
        registered_pageviews = pageviews.filter(visitor__user__isnull=False)
        registered_count = registered_pageviews.count()

        if registered_count:
            registered_unique_count = registered_pageviews.values('visitor', 'url').distinct().count()

            # Update the total unique count...
            unique_count += registered_unique_count

            stats['registered'] = {
                'total': registered_count,
                'unique': registered_unique_count,
            }

        if TRACK_ANONYMOUS_USERS and not registered_only:
            guest_pageviews = pageviews.filter(visitor__user__isnull=True)
            guest_count = guest_pageviews.count()

            if guest_count:
                guest_unique_count = guest_pageviews.values('visitor', 'url').distinct().count()

                # Update the total unique count...
                unique_count += guest_unique_count

                stats['guests'] = {
                    'total': guest_count,
                    'unique': guest_unique_count,
                }

        # Finish setting the total visitor counts
        stats['unique'] = unique_count

        return stats

