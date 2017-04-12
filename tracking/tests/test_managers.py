from __future__ import division

from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from tracking.models import Visitor, Pageview


class VisitorManagerTestCase(TestCase):

    def setUp(self):
        self.user1 = User.objects.create_user(username='foo')
        self.user2 = User.objects.create_user(username='bar')
        self.base_time = timezone.now()
        self.past = self.base_time - timedelta(hours=1)
        self.present = self.base_time
        self.future = self.base_time + timedelta(days=1)

    def _create_visits_and_views(self):
        # create a visitor with visits in the past, present, and future
        kwargs = {'ip_address':  '10.0.0.1', 'user_agent': 'django',
                  'time_on_site': 30, 'expiry_time': self.future}

        self.visitor1 = Visitor.objects.create(
            user=self.user1, start_time=self.past, session_key='A', **kwargs)
        self.visitor2 = Visitor.objects.create(
            user=self.user2, start_time=self.present, session_key='B',
            **kwargs)
        # visitor3 is in the future
        self.visitor3 = Visitor.objects.create(
            user=None, start_time=self.future, session_key='C', **kwargs)

        Pageview.objects.create(visitor=self.visitor1, view_time=self.present)
        Pageview.objects.create(visitor=self.visitor1, view_time=self.future)
        Pageview.objects.create(visitor=self.visitor2, view_time=self.past)
        Pageview.objects.create(visitor=self.visitor3, view_time=self.future)

    def test_only_anonymous(self):
        # only a guest user has visited an untracked page
        Visitor.objects.create(
            user=None, start_time=self.base_time, session_key='A',
            time_on_site=30)
        stats = Visitor.objects.stats(
            self.base_time, self.future, registered_only=True)
        expected = {
            'time_on_site': timedelta(seconds=30),
            'unique': 0,
            'total': 1,
            'return_ratio': 100.0,
            'pages_per_visit': 0
        }
        self.assertEqual(stats, expected)

    def test_visitor_stats(self):
        self._create_visits_and_views()
        start_time = self.base_time - timedelta(days=1)
        end_time = start_time + timedelta(days=2)
        stats = Visitor.objects.stats(start_time, end_time)
        self.assertEqual(stats['time_on_site'], timedelta(seconds=30))
        self.assertEqual(stats['total'], 2)
        self.assertEqual(stats['return_ratio'], 0.0)
        self.assertEqual(stats['unique'], 2)
        self.assertEqual(stats['pages_per_visit'], 3 / 2)
        registered = {
            'time_on_site': timedelta(seconds=30),
            'unique': 2,
            'total': 2,
            'return_ratio': 0.0,
            'pages_per_visit': 1.5,
        }
        self.assertEqual(stats['registered'], registered)
        guests = {
            'time_on_site': timedelta(seconds=0),
            'unique': 0,
            'total': 0,
            'return_ratio': 0.0,
            'pages_per_visit': None,
        }
        self.assertEqual(stats['guests'], guests)

        # now expand the end time to include `future` as well
        end_time = start_time + timedelta(days=3)
        stats = Visitor.objects.stats(start_time, end_time)
        self.assertEqual(stats['pages_per_visit'], 4 / 3)
        guests = {
            'time_on_site': timedelta(seconds=30),
            'unique': 1,
            'total': 1,
            'return_ratio': 0.0,
            'pages_per_visit': 1.0,
        }
        self.assertEqual(stats['guests'], guests)

    def test_visitor_stats_registered(self):
        self._create_visits_and_views()
        start_time = self.base_time - timedelta(days=1)
        end_time = start_time + timedelta(days=3)
        stats = Visitor.objects.stats(
            start_time, end_time, registered_only=True)
        self.assertEqual(stats['time_on_site'], timedelta(seconds=30))
        self.assertEqual(stats['total'], 3)
        self.assertEqual(stats['return_ratio'], (1 / 3) * 100)
        self.assertEqual(stats['unique'], 2)
        self.assertEqual(stats['pages_per_visit'], 3 / 2)
        registered = {
            'time_on_site': timedelta(seconds=30),
            'unique': 2,
            'total': 2,
            'return_ratio': 0.0,
            'pages_per_visit': 1.5,
        }
        self.assertEqual(stats['registered'], registered)
        self.assertNotIn('guests', stats)

    def test_guests(self):
        qs = Visitor.objects.guests()
        self.assertQuerysetEqual(qs, [])

        self._create_visits_and_views()
        qs = Visitor.objects.guests()
        self.assertEqual(list(qs), [self.visitor3])

    def test_registered(self):
        qs = Visitor.objects.registered()
        self.assertQuerysetEqual(qs, [])

        self._create_visits_and_views()
        qs = Visitor.objects.registered()
        self.assertEqual(list(qs), [self.visitor2, self.visitor1])

    def test_active(self):
        qs = Visitor.objects.active()
        self.assertQuerysetEqual(qs, [])

        self._create_visits_and_views()
        qs = Visitor.objects.active()
        self.assertEqual(
            list(qs),
            [self.visitor2, self.visitor1])

        qs = Visitor.objects.active(registered_only=False)
        self.assertEqual(
            list(qs),
            [self.visitor3, self.visitor2, self.visitor1])

    def test_user_stats(self):
        self._create_visits_and_views()
        # this time range should only get self.user2
        start_time = self.base_time - timedelta(minutes=1)
        end_time = start_time + timedelta(days=1)
        stats = Visitor.objects.user_stats(start_time, end_time)
        self.assertEqual(len(stats), 1)
        user = stats[0]
        self.assertEqual(user.username, self.user2.username)
        self.assertEqual(user.visit_count, 1)
        self.assertEqual(user.time_on_site, timedelta(seconds=30))
        self.assertEqual(user.pages_per_visit, 1)

        # no start_time
        stats = Visitor.objects.user_stats(None, end_time)
        self.assertEqual(len(stats), 2)

        user1 = stats[1]
        self.assertEqual(user1.username, self.user1.username)
        self.assertEqual(user1.visit_count, 1)
        self.assertEqual(user1.time_on_site, timedelta(seconds=30))
        self.assertEqual(user1.pages_per_visit, 2.0)

        user2 = stats[0]
        self.assertEqual(user2.username, self.user2.username)
        self.assertEqual(user2.visit_count, 1)
        self.assertEqual(user2.time_on_site, timedelta(seconds=30))
        self.assertEqual(user2.pages_per_visit, 1)

    def test_pageview_stats(self):
        self._create_visits_and_views()
        # full time range for this
        start_time = self.base_time - timedelta(days=1)
        end_time = start_time + timedelta(days=3)
        stats = Pageview.objects.stats(start_time, end_time)
        expected = {
            'total': 4,
            'unique': 3,
            'registered': {
                'total': 3,
                'unique': 2,
            },
            'guests': {
                'total': 1,
                'unique': 1,
            }
        }
        self.assertEqual(stats, expected)
