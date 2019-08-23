from datetime import timedelta, datetime

from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils.timezone import now

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

from tracking.admin import VisitorAdmin
from tracking.models import Visitor, Pageview


class ViewsTestCase(TestCase):

    def setUp(self):
        self.auth = {'username': 'john', 'password': 'smith'}
        self.user = User.objects.create_user(**self.auth)
        self.user.is_superuser = True
        self.user.save()
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

    def test_visitor_overview_default(self):
        # make a non PAGEVIEW tracking request
        Visitor.objects.create(
            session_key='skey',
            ip_address='127.0.0.1',
            user=self.user,
            time_on_site = 0,
        )
        response = self.client.get('/tracking/visitors/%s/' % self.user.pk)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context['user'],
            self.user)

    def test_visitor_overview_times(self):
        # make a non PAGEVIEW tracking request
        Visitor.objects.create(
            session_key='skey',
            ip_address='127.0.0.1',
            user=self.user,
            time_on_site = 0,
        )
        response = self.client.get(
            '/tracking/visitors/%s/?start=2014-11&end=2014-12-01' % self.user.pk)
        self.assertEqual(response.status_code, 200)

    def test_visitor_overview_no_records(self):
        response = self.client.get(
            '/tracking/visitors/%s/?start=2014-11&end=2014-12-01' % self.user.pk)
        # Gracefully handle when then there are o records of visits within time range
        self.assertEqual(response.status_code, 200)

    def test_visitor_overview_times_bad(self):
        # make a non PAGEVIEW tracking request
        Visitor.objects.create(
            session_key='skey',
            ip_address='127.0.0.1',
            user=self.user,
            time_on_site = 0,
        )
        response = self.client.get(
            '/tracking/visitors/%s/?start=2014-aa&end=2014-12-01' % self.user.pk)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Enter a valid date/time.')

    def test_visitor_detail_visitor_does_not_exist(self):
        response = self.client.get(
            '/tracking/visits/asdf/')
        self.assertEqual(response.status_code, 404)

    def test_visitor_detail_no_pageviews(self):
        Visitor.objects.create(
            session_key='skey',
            ip_address='127.0.0.1',
            user=self.user,
            time_on_site = 0,
        )
        response = self.client.get(
            '/tracking/visits/%s/' % self.user.pk)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['pvcount'], 0)

    def test_visitor_detail_has_pageview(self):
        visitor = Visitor.objects.create(
            session_key='skey',
            ip_address='127.0.0.1',
            user=self.user,
            time_on_site = 0,
        )
        Pageview.objects.create(
            visitor=visitor,
            url='/an/url',
            referer='/an/url',
            query_string='?a=string',
            method='PUT',
            view_time=datetime.fromtimestamp(1565033030),
        )
        response = self.client.get(
            '/tracking/visits/%s/?start=2018&end=2020' % self.user.pk)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['pageviews'].count(), 1)
        self.assertEqual(response.context['pageview_stats'].count(), 1)
        self.assertEqual(response.context['pvcount'], 1)
        self.assertEqual(response.context['visit'], visitor)

    def test_visitor_page_detail_page_does_not_exist(self):
        visitor = Visitor.objects.create(
            session_key='skey',
            ip_address='127.0.0.1',
            user=self.user,
            time_on_site = 0,
        )
        response = self.client.get(
            '/tracking/visitors/%s/page/?page_url=asdf/' % self.user.pk)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['visits'].count(), 0)
        self.assertEqual(response.context['total_views'], 0)
        self.assertEqual(response.context['avg_views_per_visit'], 0)
        self.assertEqual(response.context['visits'].count(), 1)
        self.assertEqual(response.context['user'], self.user)

    def test_visitor_page_detail_user_does_not_exist(self):
        visitor = Visitor.objects.create(
            session_key='skey',
            ip_address='127.0.0.1',
            user=self.user,
            time_on_site = 0,
        )
        pv = Pageview.objects.create(
            visitor=visitor,
            url='/an/url',
            referer='/an/url',
            query_string='?a=string',
            method='PUT',
            view_time=datetime.fromtimestamp(1565033030),
        )
        response = self.client.get(
            '/tracking/visitors/asdf/page/?page_url=%s&start=2018&end=2020' % pv.url)
        self.assertEqual(response.status_code, 404)

    def test_visitor_page_detail_one_pageview(self):
        visitor = Visitor.objects.create(
            session_key='skey',
            ip_address='127.0.0.1',
            user=self.user,
            time_on_site = 0,
        )
        pv = Pageview.objects.create(
            visitor=visitor,
            url='/an/url',
            referer='/an/url',
            query_string='?a=string',
            method='PUT',
            view_time=datetime.fromtimestamp(1565033030),
        )
        response = self.client.get(
            '/tracking/visitors/%s/page/?page_url=%s&start=2018&end=2020' % (self.user.pk, pv.url))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_views'], 1)
        self.assertEqual(response.context['avg_views_per_visit'], 1)
        self.assertEqual(response.context['visits'].count(), 1)
        self.assertEqual(response.context['user'], self.user)
        self.assertEqual(response.context['page_url'], pv.url)

    def test_visitor_pageview_pageview_does_not_exist(self):
        response = self.client.get(
            '/tracking/visitors/lkdjf/pageview/lkdjf/')
        self.assertEqual(response.status_code, 404)

    def test_visitor_pageview_one_pageview_exists(self):
        visitor = Visitor.objects.create(
            session_key='skey',
            ip_address='127.0.0.1',
            user=self.user,
            time_on_site = 0,
        )
        pv = Pageview.objects.create(
            visitor=visitor,
            url='/an/url',
            referer='/an/url',
            query_string='?a=string',
            method='PUT',
            view_time=datetime.fromtimestamp(1565033030),
        )
        response = self.client.get(
            '/tracking/visitors/%s/pageview/%s/' % (self.user.pk, pv.pk))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['pageview'], pv)
        self.assertEqual(response.context['duration'], None)

    def test_visitor_pageview_two_pageviews(self):
        visitor = Visitor.objects.create(
            session_key='skey',
            ip_address='127.0.0.1',
            user=self.user,
            time_on_site = 0,
        )
        pv1_view_time = datetime.fromtimestamp(1565033030)
        pv2_view_time = datetime.fromtimestamp(1565034030)
        pv = Pageview.objects.create(
            visitor=visitor,
            url='/an/url',
            referer='/an/url',
            query_string='?a=string',
            method='PUT',
            view_time=pv1_view_time,
        )
        Pageview.objects.create(
            visitor=visitor,
            url='/an/url',
            referer='/an/url',
            query_string='?a=string',
            method='PUT',
            view_time=pv2_view_time ,
        )
        response = self.client.get(
            '/tracking/visitors/%s/pageview/%s/' % (self.user.pk, pv.pk))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['pageview'], pv)
        self.assertEqual(response.context['duration'], pv2_view_time - pv1_view_time)

    def test_visitor_page_overview_no_pageviews(self):
        response = self.client.get(
            '/tracking/pages/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['pageview_counts'].count(), 0)
        self.assertEqual(response.context['total_page_views'], 0)
        self.assertEqual(response.context['total_pages'], 0)

    def test_visitor_page_overview_one_pageviews(self):
        visitor = Visitor.objects.create(
            session_key='skey',
            ip_address='127.0.0.1',
            user=self.user,
            time_on_site = 0,
        )
        Pageview.objects.create(
            visitor=visitor,
            url='/an/url',
            referer='/an/url',
            query_string='?a=string',
            method='PUT',
            view_time=datetime.fromtimestamp(1565033030),
        )
        response = self.client.get(
            '/tracking/pages/?start=2018&end=2020')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['pageview_counts'].count(), 1)
        self.assertEqual(response.context['total_page_views'], 1)
        self.assertEqual(response.context['total_pages'], 1)

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
