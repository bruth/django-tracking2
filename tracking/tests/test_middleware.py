import re
import sys

import django
from django.contrib.auth.models import User
from django.test import TestCase
try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

from tracking.models import Visitor, Pageview

if sys.version_info[0] == 3:
    def _u(s):
        return s
else:
    def _u(s):
        return unicode(s)

OLD_VERSION = django.VERSION < (1, 10)


class MiddlewareTestCase(TestCase):

    @patch('tracking.middleware.warnings', autospec=True)
    def test_no_session(self, mock_warnings):
        # ignore if session middleware is not present
        tracking = 'tracking.middleware.VisitorTrackingMiddleware'
        middleware = 'MIDDLEWARE_CLASSES' if OLD_VERSION else 'MIDDLEWARE'
        with self.settings(**{middleware: [tracking]}):
            self.client.get('/')
        self.assertEqual(Visitor.objects.count(), 0)
        self.assertEqual(Pageview.objects.count(), 0)
        # verify warning was issued
        msg = 'VisitorTrackingMiddleware installed withoutSessionMiddleware'
        mock_warnings.warn.assert_called_once_with(msg, RuntimeWarning)

    @patch('tracking.middleware.TRACK_AJAX_REQUESTS', False)
    def test_no_track_ajax(self):
        # ignore ajax-based requests
        self.client.get('/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(Visitor.objects.count(), 0)
        self.assertEqual(Pageview.objects.count(), 0)

    @patch('tracking.middleware.TRACK_IGNORE_STATUS_CODES', [404])
    def test_no_track_status(self):
        # ignore 404 pages
        self.client.get('invalid')
        self.assertEqual(Visitor.objects.count(), 0)
        self.assertEqual(Pageview.objects.count(), 0)

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

    def test_track_user_agent_unicode(self):
        self.client.get('/', HTTP_USER_AGENT=_u('django'))
        self.assertEqual(Visitor.objects.count(), 1)
        visitor = Visitor.objects.get()
        self.assertEqual(visitor.user_agent, 'django')

    def test_track_user_anon(self):
        self.client.get('/')
        self.assertEqual(Visitor.objects.count(), 1)
        visitor = Visitor.objects.get()
        self.assertEqual(visitor.user, None)

    def test_track_user_me(self):
        auth = {'username': 'me', 'password': 'me'}
        user = User.objects.create_user(**auth)
        self.assertTrue(self.client.login(**auth))

        self.client.get('/')
        self.assertEqual(Visitor.objects.count(), 1)
        visitor = Visitor.objects.get()
        self.assertEqual(visitor.user, user)

    @patch('tracking.middleware.TRACK_ANONYMOUS_USERS', False)
    def test_track_anonymous_users(self):
        self.client.get('/')
        self.assertEqual(Visitor.objects.count(), 0)
        self.assertEqual(Pageview.objects.count(), 0)

    @patch('tracking.middleware.TRACK_SUPERUSERS', True)
    def test_track_superusers_true(self):
        auth = {'username': 'me', 'email': 'me@me.com', 'password': 'me'}
        User.objects.create_superuser(**auth)
        self.assertTrue(self.client.login(**auth))

        self.client.get('/')
        self.assertEqual(Visitor.objects.count(), 1)
        self.assertEqual(Pageview.objects.count(), 1)

    @patch('tracking.middleware.TRACK_SUPERUSERS', False)
    def test_track_superusers_false(self):
        auth = {'username': 'me', 'email': 'me@me.com', 'password': 'me'}
        User.objects.create_superuser(**auth)
        self.assertTrue(self.client.login(**auth))

        self.client.get('/')
        self.assertEqual(Visitor.objects.count(), 0)
        self.assertEqual(Pageview.objects.count(), 0)

    def test_track_ignore_url(self):
        ignore_urls = [re.compile('foo')]
        with patch('tracking.middleware.track_ignore_urls', ignore_urls):
            self.client.get('/')
            self.client.get('/foo/')
        # tracking turns a blind eye towards ignore_urls, no visitor, no view
        self.assertEqual(Visitor.objects.count(), 1)
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
