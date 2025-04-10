##############################################################################
#
# Copyright (c) 2025 Zope Foundation and Contributors
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

from zope.component import adapter
from zope.component import provideHandler

from ...interfaces.events import IUserSessionStartedEvent
from ...tests.conformance import ICredentialsResetPlugin_conformance
from ...tests.conformance import ICredentialsUpdatePlugin_conformance
from ...tests.conformance import ILoginPasswordHostExtractionPlugin_conformance
from ...tests.test_PluggableAuthService import FauxResponse
from ...tests.test_PluggableAuthService import FauxSession


EVENTS = []


def _getTestEvents():
    global EVENTS
    return EVENTS


def _resetTestEvents():
    global EVENTS
    EVENTS = []


@adapter(IUserSessionStartedEvent)
def userSessionStartedHandler(event):
    events = _getTestEvents()
    if event not in events:
        events.append(event)


class FauxHTTPRequest:

    def __init__(self, name=None, password=None):
        self._name = name
        self._password = password
        self.RESPONSE = FauxResponse()
        self.SESSION = FauxSession()

    def _authUserPW(self):
        if self._name is None:
            return None

        return self._name, self._password

    def get(self, name, default=None):
        return getattr(self, name, default)


class SessionAuthHelperTests(unittest.TestCase,
                             ILoginPasswordHostExtractionPlugin_conformance,
                             ICredentialsResetPlugin_conformance,
                             ICredentialsUpdatePlugin_conformance):

    def _getTargetClass(self):
        from ...plugins.SessionAuthHelper import SessionAuthHelper

        return SessionAuthHelper

    def _makeOne(self, id='test', *args, **kw):
        return self._getTargetClass()(id=id, *args, **kw)

    def setUp(self):
        super().setUp()
        _resetTestEvents()

    def test_extractCredentials_no_creds(self):
        helper = self._makeOne()
        request = FauxHTTPRequest()

        self.assertEqual(helper.extractCredentials(request), {})

    def test_extractCredentials_form_creds(self):
        provideHandler(userSessionStartedHandler)
        helper = self._makeOne()
        request = FauxHTTPRequest(name='foo', password='b:ar')

        self.assertFalse(request.SESSION)
        self.assertFalse(_getTestEvents())
        self.assertEqual(helper.extractCredentials(request),
                         {'login': 'foo',
                          'password': 'b:ar',
                          'remote_host': '',
                          'remote_address': ''})
        self.assertEqual(request.SESSION['__ac_name'], 'foo')
        self.assertEqual(request.SESSION['__ac_password'], 'b:ar')
        self.assertEqual(len(_getTestEvents()), 1)

    def test_extractCredentials_session_creds(self):
        provideHandler(userSessionStartedHandler)
        helper = self._makeOne()
        request = FauxHTTPRequest()
        request.SESSION['__ac_name'] = 'foo'
        request.SESSION['__ac_password'] = 'b:ar'

        self.assertFalse(_getTestEvents())
        self.assertEqual(helper.extractCredentials(request),
                         {'login': 'foo',
                          'password': 'b:ar',
                          'remote_host': '',
                          'remote_address': ''})
        self.assertEqual(request.SESSION['__ac_name'], 'foo')
        self.assertEqual(request.SESSION['__ac_password'], 'b:ar')
        self.assertFalse(_getTestEvents())

    def test_resetCredentials(self):
        helper = self._makeOne()
        request = FauxHTTPRequest()
        request.SESSION['__ac_name'] = 'foo'
        request.SESSION['__ac_password'] = 'b:ar'

        helper.resetCredentials(request, request.RESPONSE)
        self.assertFalse(request.SESSION.get('__ac_name'))
        self.assertFalse(request.SESSION.get('__ac_password'))
        self.assertFalse(helper.extractCredentials(request))

    def test_updateCredentials_empty_session(self):
        provideHandler(userSessionStartedHandler)
        helper = self._makeOne()
        request = FauxHTTPRequest()

        self.assertFalse(request.SESSION)
        self.assertFalse(_getTestEvents())
        request.SESSION['random_key'] = '123'
        helper.updateCredentials(request, request.RESPONSE, 'foo', 'b:ar')
        self.assertEqual(request.SESSION['__ac_name'], 'foo')
        self.assertEqual(request.SESSION['__ac_password'], 'b:ar')
        self.assertEqual(request.SESSION['random_key'], '123')
        self.assertEqual(len(_getTestEvents()), 1)
        self.assertEqual(helper.extractCredentials(request),
                         {'login': 'foo',
                          'password': 'b:ar',
                          'remote_host': '',
                          'remote_address': ''})
        self.assertEqual(len(_getTestEvents()), 1)

    def test_updateCredentials_existing_session(self):
        provideHandler(userSessionStartedHandler)
        helper = self._makeOne()
        request = FauxHTTPRequest()
        request.SESSION['__ac_name'] = 'foo'
        request.SESSION['__ac_password'] = 'b:ar'
        request.SESSION['random_key'] = '123'

        self.assertFalse(_getTestEvents())
        helper.updateCredentials(request, request.RESPONSE, 'foo', 'b:az')
        self.assertEqual(request.SESSION['__ac_name'], 'foo')
        self.assertEqual(request.SESSION['__ac_password'], 'b:az')
        self.assertEqual(request.SESSION['random_key'], '123')
        self.assertEqual(helper.extractCredentials(request),
                         {'login': 'foo',
                          'password': 'b:az',
                          'remote_host': '',
                          'remote_address': ''})
        self.assertFalse(_getTestEvents())

    def test_updateCredentials_existing_session_new_login(self):
        # If the login name changes a new login session is assumed.
        provideHandler(userSessionStartedHandler)
        helper = self._makeOne()
        request = FauxHTTPRequest()
        request.SESSION['__ac_name'] = 'foo'
        request.SESSION['__ac_password'] = 'b:ar'
        request.SESSION['random_key'] = '123'

        self.assertFalse(_getTestEvents())
        helper.updateCredentials(request, request.RESPONSE, 'bar', 'b:az')
        self.assertEqual(request.SESSION['__ac_name'], 'bar')
        self.assertEqual(request.SESSION['__ac_password'], 'b:az')
        self.assertEqual(request.SESSION['random_key'], '123')
        self.assertEqual(helper.extractCredentials(request),
                         {'login': 'bar',
                          'password': 'b:az',
                          'remote_host': '',
                          'remote_address': ''})
        self.assertEqual(len(_getTestEvents()), 1)

    def test_updateCredentials_clears_session(self):
        provideHandler(userSessionStartedHandler)
        helper = self._makeOne()
        helper.clear_session_on_login = True  # Turn on clearing session
        request = FauxHTTPRequest()
        request.SESSION['random_key'] = '123'

        self.assertFalse(_getTestEvents())
        helper.updateCredentials(request, request.RESPONSE, 'bar', 'b:az')
        self.assertEqual(request.SESSION['__ac_name'], 'bar')
        self.assertEqual(request.SESSION['__ac_password'], 'b:az')
        with self.assertRaises(KeyError):
            request.SESSION['random_key']
        self.assertEqual(helper.extractCredentials(request),
                         {'login': 'bar',
                          'password': 'b:az',
                          'remote_host': '',
                          'remote_address': ''})
        self.assertEqual(len(_getTestEvents()), 1)
