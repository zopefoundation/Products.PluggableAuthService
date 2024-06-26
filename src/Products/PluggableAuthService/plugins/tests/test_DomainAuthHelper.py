##############################################################################
#
# Copyright (c) 2006 Zope Foundation and Contributors
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this
# distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
import unittest

from ...tests.conformance import IAuthenticationPlugin_conformance
from ...tests.conformance import IExtractionPlugin_conformance
from ...tests.conformance import IRolesPlugin_conformance


try:
    from IPy import IP
except ModuleNotFoundError:
    IP = None


class FauxRequest:

    def __init__(self, **kw):
        self._data = dict(kw)

    def get(self, key, default=None):
        return self._data.get(key, default)


class FauxRequestWithClientAddr(FauxRequest):

    def getClientAddr(self):
        return self._data.get('CLIENT_ADDR')


class DomainAuthHelperTests(unittest.TestCase, IExtractionPlugin_conformance,
                            IAuthenticationPlugin_conformance,
                            IRolesPlugin_conformance):

    def _getTargetClass(self):

        from ...plugins.DomainAuthHelper import DomainAuthHelper

        return DomainAuthHelper

    def _makeOne(self, id='test', *args, **kw):

        return self._getTargetClass()(id=id, *args, **kw)

    def test_extractCredentials_no_creds(self):

        helper = self._makeOne()
        request = FauxRequest()

        self.assertEqual(helper.extractCredentials(request), {})

    def test_extractCredentials_with_getClientAddr(self):

        helper = self._makeOne()
        request = FauxRequestWithClientAddr(REMOTE_HOST='foo',
                                            CLIENT_ADDR='bar')

        self.assertEqual(helper.extractCredentials(request), {
            'remote_host': 'foo',
            'remote_address': 'bar'
        })

    def test_extractCredentials_no_getClientAddr_with_REMOTE_ADDR(self):

        helper = self._makeOne()
        request = FauxRequest(REMOTE_HOST='foo', REMOTE_ADDR='bam')

        self.assertEqual(helper.extractCredentials(request), {
            'remote_host': 'foo',
            'remote_address': 'bam'
        })

    def test_extractCredentials_with_getClientAddr_no_REMOTE_HSOT(self):

        helper = self._makeOne()
        request = FauxRequestWithClientAddr(CLIENT_ADDR='bar')

        self.assertEqual(helper.extractCredentials(request), {
            'remote_host': '',
            'remote_address': 'bar'
        })

    def test_extractCredentials_with_REMOTE_ADDR_no_REMOTE_HOST(self):

        helper = self._makeOne()
        request = FauxRequest(REMOTE_ADDR='bam')

        self.assertEqual(helper.extractCredentials(request), {
            'remote_host': '',
            'remote_address': 'bam'
        })

    def test_extractCredentials_no_getClientAddr_no_REMOTE_ADDR(self):

        helper = self._makeOne()
        request = FauxRequest(REMOTE_HOST='foo')

        self.assertEqual(helper.extractCredentials(request), {
            'remote_host': 'foo',
            'remote_address': ''
        })

    def test_authenticateCredentials_empty_mapping_empty_creds(self):
        creds = {}
        helper = self._makeOne()
        self.assertEqual(helper.authenticateCredentials(creds), (None, None))

    def test_authenticateCredentials_empty_mapping_nonesuch_remote_host(self):
        creds = {'remote_host': 'foo'}
        helper = self._makeOne()
        self.assertEqual(helper.authenticateCredentials(creds), (None, None))

    def test_authenticateCredentials_empty_mapping_nonesuch_remote_addr(self):
        creds = {'remote_address': 'bam'}
        helper = self._makeOne()
        self.assertEqual(helper.authenticateCredentials(creds), (None, None))

    def test_authenticateCredentials_w_mapping_known_remote_host(self):
        creds = {'login': 'qux', 'remote_host': 'bam'}
        helper = self._makeOne()
        helper.manage_addMapping(match_type='equals', match_string='bam')

        self.assertEqual(helper.authenticateCredentials(creds), ('qux', 'qux'))

    def test_authenticateCredentials_w_mapping_known_remote_addr(self):
        creds = {'login': 'qux', 'remote_address': 'baz'}
        helper = self._makeOne()
        helper.manage_addMapping(match_type='endswith',
                                 match_string='z',
                                 username='foo')

        self.assertEqual(helper.authenticateCredentials(creds), ('qux', 'qux'))

    def test_authenticateCredentials_w_mapping_no_login_known_remote_hst(self):
        creds = {'remote_host': 'baz'}
        helper = self._makeOne()
        helper.manage_addMapping(match_type='equals',
                                 match_string='baz',
                                 username='foo')

        self.assertEqual(helper.authenticateCredentials(creds), ('foo', 'foo'))

    # ???  add tests for getRolesForPrincipal, etc.


class EqualsFilterTests(unittest.TestCase):

    def _getTargetClass(self):
        from ...plugins.DomainAuthHelper import EqualsFilter
        return EqualsFilter

    def _makeOne(self, matchstring):
        return self._getTargetClass()(matchstring)

    def test_hit(self):
        filter = self._makeOne('hitme')
        self.assertTrue(filter('hitme'))

    def test_miss(self):
        filter = self._makeOne('hitme')
        self.assertFalse(filter('miss'))


class StartsWithFilterTests(unittest.TestCase):

    def _getTargetClass(self):
        from ...plugins.DomainAuthHelper import StartsWithFilter
        return StartsWithFilter

    def _makeOne(self, matchstring):
        return self._getTargetClass()(matchstring)

    def test_hit_exact(self):
        filter = self._makeOne('hitme')
        self.assertTrue(filter('hitme'))

    def test_hit_prefix(self):
        filter = self._makeOne('hit')
        self.assertTrue(filter('hitme'))

    def test_miss(self):
        filter = self._makeOne('hitme')
        self.assertFalse(filter('miss'))


class EndsWithFilterTests(unittest.TestCase):

    def _getTargetClass(self):
        from ...plugins.DomainAuthHelper import EndsWithFilter
        return EndsWithFilter

    def _makeOne(self, matchstring):
        return self._getTargetClass()(matchstring)

    def test_hit_exact(self):
        filter = self._makeOne('hitme')
        self.assertTrue(filter('hitme'))

    def test_hit_suffix(self):
        filter = self._makeOne('tme')
        self.assertTrue(filter('hitme'))

    def test_miss(self):
        filter = self._makeOne('hitme')
        self.assertFalse(filter('miss'))


class RegexFilterTests(unittest.TestCase):

    def _getTargetClass(self):
        from ...plugins.DomainAuthHelper import RegexFilter
        return RegexFilter

    def _makeOne(self, matchstring):
        return self._getTargetClass()(matchstring)

    def test_hit_exact(self):
        filter = self._makeOne('^hitme$')
        self.assertTrue(filter('hitme'))

    def test_hit_pattern(self):
        filter = self._makeOne('^h.*tme$')
        self.assertTrue(filter('hitme'))

    def test_miss(self):
        filter = self._makeOne('^hitme$')
        self.assertFalse(filter('miss'))


class IPFilterTests(unittest.TestCase):

    def _getTargetClass(self):
        from ...plugins.DomainAuthHelper import IPFilter
        return IPFilter

    def _makeOne(self, matchstring):
        return self._getTargetClass()(matchstring)

    def test_hit_exact(self):
        filter = self._makeOne('192.168.1.24')
        self.assertTrue(filter('192.168.1.24'))

    def test_miss_exact(self):
        filter = self._makeOne('192.168.1.24')
        self.assertFalse(filter('192.168.1.13'))

    def test_hit_prefix(self):
        filter = self._makeOne('192.168.1.0/24')
        self.assertTrue(filter('192.168.1.13'))

    def test_miss_prefix(self):
        filter = self._makeOne('192.168.1.0/24')
        self.assertFalse(filter('192.168.0.13'))

    def test_hit_range(self):
        filter = self._makeOne('192.168.1.0-192.168.1.255')
        self.assertTrue(filter('192.168.1.13'))

    def test_miss_range(self):
        filter = self._makeOne('192.168.1.0-192.168.1.255')
        self.assertFalse(filter('192.168.0.13'))


def test_suite():
    loadTestsFromTestCase = unittest.defaultTestLoader.loadTestsFromTestCase
    tests = (loadTestsFromTestCase(DomainAuthHelperTests),
             loadTestsFromTestCase(EqualsFilterTests),
             loadTestsFromTestCase(StartsWithFilterTests),
             loadTestsFromTestCase(EndsWithFilterTests),
             loadTestsFromTestCase(RegexFilterTests))

    if IP is not None:
        tests += (loadTestsFromTestCase(IPFilterTests), )

    return unittest.TestSuite(tests)
