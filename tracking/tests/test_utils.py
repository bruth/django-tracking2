from django.test import TestCase

from tracking.utils import _is_valid_ipv4_address, _is_valid_ipv6_address


class UtilsTestCase(TestCase):

    def test__is_valid_ipv4_address(self):
        self.assertTrue(_is_valid_ipv4_address('10.1.1.1'))
        self.assertTrue(_is_valid_ipv4_address('255.255.255.255'))
        self.assertTrue(_is_valid_ipv4_address('0.0.0.0'))

        self.assertFalse(_is_valid_ipv4_address('256.0.0.257'))
        self.assertFalse(_is_valid_ipv4_address('25600257'))

    def test__is_valid_ipv6_address(self):
        valid_addrs = (
            'ABCD:EF01:2345:6789:ABCD:EF01:2345:6789',
            '2001:DB8:0:0:8:800:200C:417A',
            'FF01:0:0:0:0:0:0:101',
            '0:0:0:0:0:0:0:1',
            '0:0:0:0:0:0:0:0',
            '2001:DB8::8:800:200C:417A',
            'FF01::101',
            '::1',
            '::',
            '0:0:0:0:0:0:13.1.68.3',
            '0:0:0:0:0:FFFF:129.144.52.38',
            '::13.1.68.3',
            '::FFFF:129.144.52.38',
            '2001:0DB8:0000:CD30:0000:0000:0000:0000',
            '2001:0DB8::CD30:0:0:0:0',
            '2001:0DB8:0:CD30::',
        )
        for addr in valid_addrs:
            self.assertTrue(_is_valid_ipv6_address(addr), addr)

        invalid_addrs = (
            '2001:0DB8:0:CD3',
            '2001::0DB8::CD30',
        )
        for addr in invalid_addrs:
            self.assertFalse(_is_valid_ipv6_address(addr), addr)
