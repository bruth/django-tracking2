from datetime import timedelta

import django
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils.timezone import now

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

try:
    from unittest import skipIf
except ImportError:
    # python2.6 doesn't have unittest.skip*
    from unittest2 import skipIf

from tracking.admin import VisitorAdmin
from tracking.models import Visitor

dj_version = django.get_version()


class ViewsTestCase(TestCase):

    def setUp(self):
        self.auth = {'username': 'john', 'password': 'smith'}
        user = User.objects.create_user(**self.auth)
        user.is_superuser = True
        user.save()
        self.assertTrue(self.client.login(**self.auth))

    def test_dashboard_default(self):
        # make a non PAGEVIEW tracking request
        response = self.client.get('/tracking/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context['pageview_stats'],
            {'unique': 0, 'total': 0})

    @patch('tracking.views.TRACK_PAGEVIEWS', False)
    def test_dashboard_default_no_views(self):
        # make a non PAGEVIEW tracking request
        response = self.client.get('/tracking/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['pageview_stats'], None)

    def test_dashboard_times(self):
        # make a non PAGEVIEW tracking request
        response = self.client.get(
            '/tracking/?start=2014-11&end=2014-12-01')
        self.assertEqual(response.status_code, 200)

    def test_dashboard_times_bad(self):
        # make a non PAGEVIEW tracking request
        response = self.client.get(
            '/tracking/?start=2014-aa&end=2014-12-01')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Enter a valid date/time.')

    @skipIf(dj_version < '1.6', 'django < 1.6 test client does not logout')
    @patch('tracking.handlers.timezone.now', autospec=True)
    def test_logout_tracking(self, mock_end):
        # logout should call post-logout signal
        self.now = now()
        mock_end.return_value = self.now

        # ... but we didn't touch the site
        self.client.logout()
        self.assertEqual(Visitor.objects.count(), 0)

        # ... now we have!
        self.client.login(**self.auth)
        self.client.get('/tracking/')
        self.client.logout()

        self.assertEqual(Visitor.objects.count(), 1)
        visitor = Visitor.objects.get()
        self.assertEqual(visitor.end_time, self.now)
        self.assertTrue(visitor.time_on_site > 0)


class AdminViewTestCase(TestCase):

    def setUp(self):
        self.site = AdminSite()

    @patch('tracking.middleware.TRACK_PAGEVIEWS', True)
    def test_admin(self):
        visitor = Visitor.objects.create()
        admin = VisitorAdmin(Visitor, self.site)
        self.assertFalse(admin.session_over(visitor))
        visitor.expiry_time = now() - timedelta(seconds=10)
        self.assertTrue(admin.session_over(visitor))
        visitor.expiry_time = None
        visitor.end_time = now()
        self.assertTrue(admin.session_over(visitor))

        time_on_site = None
        self.assertEqual(admin.pretty_time_on_site(visitor), time_on_site)

        visitor.time_on_site = 30
        time_on_site = timedelta(seconds=30)
        self.assertEqual(admin.pretty_time_on_site(visitor), time_on_site)
