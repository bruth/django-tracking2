from django.test import TestCase
from django.contrib.auth.models import User


class ViewsTestCase(TestCase):

    def setUp(self):
        self.auth = {'username': 'john', 'password': 'smith'}
        user = User.objects.create_user(**self.auth)
        user.is_superuser = True
        user.save()
        self.assertTrue(self.client.login(**self.auth))

    def test_dashboard_default(self):
        # make a non PAGEVIEW tracking request
        response = self.client.get('/tracking/dashboard/')
        self.assertEqual(response.status_code, 200)

    def test_dashboard_times(self):
        # make a non PAGEVIEW tracking request
        response = self.client.get(
            '/tracking/dashboard/?start=2014-11&end=2014-12-01')
        self.assertEqual(response.status_code, 200)
