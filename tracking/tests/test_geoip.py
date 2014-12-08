from os import getenv
from unittest import skipUnless
from django.test import TestCase
from mock import patch
from django.contrib.gis.geoip import HAS_GEOIP
if HAS_GEOIP:
    from django.contrib.gis.geoip import GeoIPException

from tracking.models import Visitor


class GeoIPTestCase(TestCase):

    def test_geoip_none(self):
        v = Visitor.objects.create(ip_address='8.8.8.8')  # sorry Google
        self.assertEqual(v.geoip_data, None)

    @skipUnless(getenv('CI'), 'cannot guarantee location of GeoIP data')
    @patch('tracking.models.TRACK_USING_GEOIP', True)
    def test_geoip(self):
        v = Visitor.objects.create(ip_address='64.17.254.216')
        expected = {
            'city': u'El Segundo',
            'continent_code': u'NA',
            'region': u'CA',
            'charset': 0,
            'area_code': 310,
            'longitude': -118.40399932861328,
            'country_code3': u'USA',
            'latitude': 33.91640090942383,
            'postal_code': u'90245',
            'dma_code': 803,
            'country_code': u'US',
            'country_name': u'United States'
        }
        self.assertEqual(v.geoip_data, expected)
        # do it again, to verify the cached version hits
        self.assertEqual(v.geoip_data, expected)

    @patch('tracking.models.TRACK_USING_GEOIP', True)
    def test_geoip_exc(self):
        with patch('tracking.models.GeoIP', autospec=True) as mock_geo:
            mock_geo.side_effect = GeoIPException('bad data')
            v = Visitor.objects.create(ip_address='64.17.254.216')
            self.assertEqual(v.geoip_data, None)
