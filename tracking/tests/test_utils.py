from django.test import TestCase
try:
    from unittest.mock import Mock
except ImportError:
    from mock import Mock

from tracking.utils import get_ip_address


class UtilsTestCase(TestCase):
    def test_get_ip_address(self):
        r = Mock(META={})
        self.assertEqual(get_ip_address(r), None)
        r = Mock(META={'REMOTE_ADDR': '2001:0DB8:0:CD30::'})
        self.assertEqual(get_ip_address(r), '2001:0DB8:0:CD30::')
        r = Mock(META={'HTTP_X_CLUSTERED_CLIENT_IP': '10.0.0.1, 10.1.1.1'})
        self.assertEqual(get_ip_address(r), '10.0.0.1')
