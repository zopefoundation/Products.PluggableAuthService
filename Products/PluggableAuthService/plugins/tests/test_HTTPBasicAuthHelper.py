##############################################################################
#
# Copyright (c) 2001 Zope Foundation and Contributors
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
from Products.PluggableAuthService.tests import conformance


class FauxHTTPRequest:

    def __init__(self, name=None, password=None):

        self._name = name
        self._password = password

    def _authUserPW(self):

        if self._name is None:
            return None

        return self._name, self._password

    def get(self, name, default=None):
        return getattr(self, name, default)


class FauxHTTPResponse:

    _unauthorized_called = 0
    realm = 'unit test'
    headers = {}

    def unauthorized(self):

        self._unauthorized_called = 1

    def setStatus(self, status, reason=None):

        self.status = status

    def setHeader(self, name, value, literal=0):

        self.headers[name] = value

    def addHeader(self, name, value):
        previous = self.headers.get(name)
        if previous:
            self.headers[name] = [previous, value]
        else:
            self.headers[name] = value

    def setBody(self, body, is_error=0):
        self.body = body


class HTTPBasicAuthHelperTests(
    unittest.TestCase,
    conformance.ILoginPasswordHostExtractionPlugin_conformance,
    conformance.IChallengePlugin_conformance,
    conformance.ICredentialsResetPlugin_conformance
):

    def _getTargetClass(self):

        from Products.PluggableAuthService.plugins.HTTPBasicAuthHelper \
            import HTTPBasicAuthHelper

        return HTTPBasicAuthHelper

    def _makeOne(self, id='test', *args, **kw):

        return self._getTargetClass()(id=id, *args, **kw)

    def test_extractCredentials_no_creds(self):

        helper = self._makeOne()
        request = FauxHTTPRequest()

        self.assertEqual(helper.extractCredentials(request), {})

    def test_extractCredentials_with_creds(self):

        helper = self._makeOne()
        request = FauxHTTPRequest('foo', 'bar')

        self.assertEqual(
            helper.extractCredentials(request),
            {
                'login': 'foo',
                'password': 'bar',
                'remote_host': '',
                'remote_address': ''
            }
        )

    def test_challenge(self):
        helper = self._makeOne()
        request = FauxHTTPRequest()
        response = FauxHTTPResponse()

        self.failIf(response._unauthorized_called)
        helper.challenge(request, response)
        self.failUnless(response.status, 401)
        self.failUnless(response.headers['WWW-Authenticate'],
                        'basic realm="unit test"')

    def test_multi_challenge(self):
        # It is possible for HTTP headers to contain multiple auth headers
        helper = self._makeOne()
        request = FauxHTTPRequest()
        response = FauxHTTPResponse()

        self.failIf(response._unauthorized_called)
        helper.challenge(request, response)

        response.realm = 'second realm'
        helper.challenge(request, response)

        self.failUnless(response.status, 401)
        self.failUnless(
            response.headers['WWW-Authenticate'],
            ['basic realm="unit test"', 'basic realm="second realm"']
        )

    def test_resetCredentials(self):

        helper = self._makeOne()
        request = FauxHTTPRequest()
        response = FauxHTTPResponse()

        self.failIf(response._unauthorized_called)
        helper.resetCredentials(request, response)
        self.failUnless(response._unauthorized_called)

if __name__ == "__main__":
    unittest.main()


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(HTTPBasicAuthHelperTests),
    ))
