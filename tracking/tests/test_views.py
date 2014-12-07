from django.test import TestCase
from django.contrib.auth.models import User
from django.utils.timezone import now
from mock import patch

from tracking.models import Visitor


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

    def test_dashboard_times(self):
        # make a non PAGEVIEW tracking request
        response = self.client.get(
            '/tracking/?start_time=2014-11&end_time=2014-12-01')
        self.assertEqual(response.status_code, 200)

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
