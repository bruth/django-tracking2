import re

from django.test import TestCase
from mock import patch

from tracking.models import Visitor, Pageview


class MiddlewareTestCase(TestCase):

    @patch('tracking.middleware.TRACK_PAGEVIEWS', False)
    def test_no_track_pageviews(self):
        # make a non PAGEVIEW tracking request
        self.client.get('/')
        self.assertEqual(Visitor.objects.count(), 1)
        self.assertEqual(Pageview.objects.count(), 0)

    @patch('tracking.middleware.TRACK_PAGEVIEWS', True)
    def test_track_pageviews(self):
        self.client.get('/')
        self.assertEqual(Visitor.objects.count(), 1)
        self.assertEqual(Pageview.objects.count(), 1)

    def test_track_user_agent(self):
        self.client.get('/', HTTP_USER_AGENT='django')
        self.assertEqual(Visitor.objects.count(), 1)
        visitor = Visitor.objects.get()
        self.assertEqual(visitor.user_agent, 'django')

    @patch('tracking.middleware.TRACK_ANONYMOUS_USERS', False)
    def test_track_anonymous_users(self):
        self.client.get('/')
        self.assertEqual(Visitor.objects.count(), 0)
        self.assertEqual(Pageview.objects.count(), 0)

    @patch('tracking.middleware.TRACK_PAGEVIEWS', True)
    def test_track_pageviews_ignore_url(self):
        ignore_urls = [re.compile('foo')]
        with patch('tracking.middleware.track_ignore_urls', ignore_urls):
            self.client.get('/')
            self.client.get('/foo/')
        # Vistor is still tracked, but page is not (in second case
        self.assertEqual(Visitor.objects.count(), 2)
        self.assertEqual(Pageview.objects.count(), 1)

    @patch('tracking.middleware.TRACK_PAGEVIEWS', True)
    @patch('tracking.middleware.TRACK_REFERER', True)
    @patch('tracking.middleware.TRACK_QUERY_STRING', True)
    def test_track_referer_string(self):
        self.client.get('/?foo=bar&baz=bin', HTTP_REFERER='http://foo/bar')
        # Vistor is still tracked, but page is not (in second case
        self.assertEqual(Visitor.objects.count(), 1)
        self.assertEqual(Pageview.objects.count(), 1)
        view = Pageview.objects.get()
        self.assertEqual(view.referer, 'http://foo/bar')
        self.assertEqual(view.query_string, 'foo=bar&baz=bin')
