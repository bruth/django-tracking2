from django.test import TestCase

from tracking.models import Visitor, Pageview


class TrackingTestCase(TestCase):

    def test_fun(self):
        # make a single request and verify that it was tracked
        self.client.get('/')
        self.assertEqual(Visitor.objects.count(), 1)
        self.assertEqual(Pageview.objects.count(), 1)
