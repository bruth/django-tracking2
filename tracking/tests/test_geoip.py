from os import getenv
from django.test import TestCase
from unittest.mock import patch

from django.contrib.gis.geoip2 import HAS_GEOIP2
if HAS_GEOIP2:
    from django.contrib.gis.geoip2 import GeoIP2Exception

from unittest import skipUnless

from tracking.models import Visitor  # noqa


class GeoIPTestCase(TestCase):

    def test_geoip_none(self):
        v = Visitor.objects.create(ip_address='8.8.8.8')  # sorry Google
        self.assertEqual(v.geoip_data, None)

    @skipUnless(getenv('CI'), 'cannot guarantee location of GeoIP data')
    @patch('tracking.models.TRACK_USING_GEOIP', True)
    def test_geoip_django_1x(self):
        v = Visitor.objects.create(ip_address='64.17.254.216')
        expected = {
            'city': 'El Segundo',
            'continent_code': 'NA',
            'region': 'CA',
            'charset': 0,
            'area_code': 310,
            'longitude': -118.40399932861328,
            'country_code3': 'USA',
            'latitude': 33.91640090942383,
            'postal_code': '90245',
            'dma_code': 803,
            'country_code': 'US',
            'country_name': 'United States'
        }

        self.assertEqual(v.geoip_data, expected)
        # do it again, to verify the cached version hits
        self.assertEqual(v.geoip_data, expected)

    @skipUnless(getenv('CI'), 'cannot guarantee location of GeoIP data')
    @patch('tracking.models.TRACK_USING_GEOIP', True)
    def test_geoip2_django_20(self):
        v = Visitor.objects.create(ip_address='81.2.69.160')
        expected = {
            'city': 'London',
            'country_code': 'GB',
            'country_name': 'United Kingdom',
            'dma_code': None,
            'latitude': 51.5142,
            'longitude': -0.0931,
            'postal_code': None,
            'region': 'ENG',
            'time_zone': 'Europe/London'
        }

        self.assertEqual(v.geoip_data, expected)
        # do it again, to verify the cached version hits
        self.assertEqual(v.geoip_data, expected)

    @skipUnless(getenv('CI'), 'cannot guarantee location of GeoIP data')
    @patch('tracking.models.TRACK_USING_GEOIP', True)
    def test_geoip2_django_21(self):
        v = Visitor.objects.create(ip_address='81.2.69.160')
        expected = {
            'city': 'London',
            'country_code': 'GB',
            'continent_code': 'EU',
            'continent_name': 'Europe',
            'country_name': 'United Kingdom',
            'dma_code': None,
            'latitude': 51.5142,
            'longitude': -0.0931,
            'postal_code': None,
            'region': 'ENG',
            'time_zone': 'Europe/London'
        }

        self.assertEqual(v.geoip_data, expected)
        # do it again, to verify the cached version hits
        self.assertEqual(v.geoip_data, expected)

    @patch('tracking.models.TRACK_USING_GEOIP', True)
    def test_geoip_exc(self):
        with patch('tracking.models.GeoIP2', autospec=True) as mock_geo:
            mock_geo.side_effect = GeoIP2Exception('bad data')
            v = Visitor.objects.create(ip_address='64.17.254.216')
            self.assertEqual(v.geoip_data, None)
