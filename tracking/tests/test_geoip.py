import sys
import django

from os import getenv
from django.test import TestCase
try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

from django.contrib.gis.geoip import HAS_GEOIP
if HAS_GEOIP:
    from django.contrib.gis.geoip import GeoIPException
try:
    from unittest import skipUnless, skipIf
except ImportError:
    # python2.6 doesn't have unittest.skip*
    from unittest2 import skipUnless, skipIf

from tracking.models import Visitor

# django 1.5 combined with python 3+ doesn't work, so skip it
dj_version = django.get_version()
broken_geoip = (dj_version[:3] == '1.5') and (sys.version_info[0] == 3)


class GeoIPTestCase(TestCase):

    def test_geoip_none(self):
        v = Visitor.objects.create(ip_address='8.8.8.8')  # sorry Google
        self.assertEqual(v.geoip_data, None)

    @skipIf(dj_version[:3] == '1.5', 'django 1.5 has GeoIP parsing issues')
    @skipUnless(getenv('CI'), 'cannot guarantee location of GeoIP data')
    @patch('tracking.models.TRACK_USING_GEOIP', True)
    def test_geoip(self):
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

    @patch('tracking.models.TRACK_USING_GEOIP', True)
    def test_geoip_exc(self):
        with patch('tracking.models.GeoIP', autospec=True) as mock_geo:
            mock_geo.side_effect = GeoIPException('bad data')
            v = Visitor.objects.create(ip_address='64.17.254.216')
            self.assertEqual(v.geoip_data, None)
