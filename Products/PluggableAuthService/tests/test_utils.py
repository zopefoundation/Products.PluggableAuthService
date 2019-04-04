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

import six


class Test_createViewName(unittest.TestCase):

    def _callFUT(self, *args, **kw):
        from Products.PluggableAuthService.utils import createViewName
        return createViewName(*args, **kw)

    def test_simple(self):
        self.assertEqual(self._callFUT('foo', 'bar'), b'foo-bar')

    def test_no_user_handle(self):
        self.assertEqual(self._callFUT('foo', None), b'foo')

    def test_latin1_umlaut_in_method(self):
        self.assertEqual(self._callFUT(u'f\366o'), b'f\xc3\xb6o')

    def test_utf8_umlaut_in_method(self):
        self.assertEqual(self._callFUT(b'f\303\266o'), b'f\303\266o')

    def test_unicode_umlaut_in_method(self):
        self.assertEqual(self._callFUT(u'f\366o'), b'f\xc3\xb6o')

    def test_latin1_umlaut_in_handle(self):
        self.assertEqual(self._callFUT('foo', u'b\344r'), b'foo-b\xc3\xa4r')

    def test_utf8_umlaut_in_handle(self):
        self.assertEqual(self._callFUT('foo', b'b\303\244r'),
                         b'foo-b\xc3\xa4r')

    def test_unicode_umlaut_in_handle(self):
        self.assertEqual(self._callFUT('foo', u'b\344r'), b'foo-b\303\244r')


class Test_createKeywords(unittest.TestCase):

    def _callFUT(self, *args, **kw):
        from Products.PluggableAuthService.utils import createKeywords
        return createKeywords(*args, **kw)

    def test_simple(self):
        _ITEMS = (('foo', 'bar'),)
        hashed = _createHashedValue(_ITEMS)
        self.assertEqual(self._callFUT(foo='bar'),
                         {'keywords': hashed})

    def test_createKeywords_multiple(self):
        _ITEMS = (('foo', 'bar'), ('baz', 'peng'))
        hashed = _createHashedValue(_ITEMS)
        self.assertEqual(self._callFUT(foo='bar', baz='peng'),
                         {'keywords': hashed})

    def test_createKeywords_latin1_umlaut(self):
        _ITEMS = (('foo', 'bar'), ('baz', 'M\344dchen'))
        hashed = _createHashedValue(_ITEMS)
        self.assertEqual(self._callFUT(foo='bar', baz='M\344dchen'),
                         {'keywords': hashed})

    def test_createKeywords_utf8_umlaut(self):
        _ITEMS = (('foo', 'bar'), ('baz', 'M\303\244dchen'))
        hashed = _createHashedValue(_ITEMS)
        self.assertEqual(self._callFUT(foo='bar', baz='M\303\244dchen'),
                         {'keywords': hashed})

    def test_createKeywords_unicode_umlaut(self):
        _ITEMS = (('foo', 'bar'), ('baz', u'M\344dchen'))
        hashed = _createHashedValue(_ITEMS)
        self.assertEqual(self._callFUT(foo='bar', baz=u'M\344dchen'),
                         {'keywords': hashed})

    def test_createKeywords_utf16_umlaut(self):
        _ITEMS = (('foo', 'bar'), ('baz', u'M\344dchen'.encode('utf-16')))
        hashed = _createHashedValue(_ITEMS)
        self.assertEqual(self._callFUT(foo='bar',
                                       baz=u'M\344dchen'.encode('utf-16')),
                         {'keywords': hashed})

    def test_createKeywords_unicode_chinese(self):
        _ITEMS = (('foo', 'bar'), ('baz', u'\u03a4\u03b6'))
        hashed = _createHashedValue(_ITEMS)
        self.assertEqual(self._callFUT(foo='bar', baz=u'\u03a4\u03b6'),
                         {'keywords': hashed})


def _makeRequestWSession(**session):
    from zope.interface import implementer
    from zope.publisher.interfaces.browser import IBrowserRequest

    @implementer(IBrowserRequest)
    class _Request(dict):
        pass

    request = _Request()
    request.SESSION = session.copy()
    request.form = {}
    return request


class Test_getCSRFToken(unittest.TestCase):

    def _callFUT(self, *args, **kw):
        from Products.PluggableAuthService.utils import getCSRFToken
        return getCSRFToken(*args, **kw)

    def test_wo_token_in_request(self):
        request = _makeRequestWSession()
        token = self._callFUT(request)
        self.assertTrue(isinstance(token, str))
        self.assertFalse(set(token) - set('0123456789abcdef'))

    def test_w_token_in_request(self):
        request = _makeRequestWSession()
        request.SESSION['_csrft_'] = 'deadbeef'
        token = self._callFUT(request)
        self.assertEqual(token, 'deadbeef')

    def test_session_fails_truth_test(self):
        # Some session implementations may not be recognized as
        # valid sessions because when empty they fail a simple truth test.
        # Using a dict here as an example.
        request = _makeRequestWSession()
        request.SESSION = {}
        self._callFUT(request)

        # After the call, the returned token must also be in the session
        # if getCSRFToken has recognized our session as such.
        self.assertIn('_csrft_', request.SESSION)


class Test_checkCSRFToken(unittest.TestCase):

    def _callFUT(self, *args, **kw):
        from Products.PluggableAuthService.utils import checkCSRFToken
        return checkCSRFToken(*args, **kw)

    def test_wo_token_in_session_or_form_w_raises(self):
        from zExceptions import Forbidden
        request = _makeRequestWSession()
        self.assertRaises(Forbidden, self._callFUT, request)

    def test_wo_token_in_session_or_form_wo_raises(self):
        request = _makeRequestWSession()
        self.assertFalse(self._callFUT(request, raises=False))

    def test_wo_token_in_session_w_token_in_form_w_raises(self):
        from zExceptions import Forbidden
        request = _makeRequestWSession()
        request.form['csrf_token'] = 'deadbeef'
        self.assertRaises(Forbidden, self._callFUT, request)

    def test_wo_token_in_session_w_token_in_form_wo_raises(self):
        request = _makeRequestWSession()
        request.form['csrf_token'] = 'deadbeef'
        self.assertFalse(self._callFUT(request, raises=False))

    def test_w_token_in_session_wo_token_in_form_w_raises(self):
        from zExceptions import Forbidden
        request = _makeRequestWSession(_csrft_='deadbeef')
        self.assertRaises(Forbidden, self._callFUT, request)

    def test_w_token_in_session_wo_token_in_form_wo_raises(self):
        request = _makeRequestWSession(_csrft_='deadbeef')
        self.assertFalse(self._callFUT(request, raises=False))

    def test_w_token_in_session_w_token_in_form_miss_w_raises(self):
        from zExceptions import Forbidden
        request = _makeRequestWSession(_csrft_='deadbeef')
        request.form['csrf_token'] = 'bab3l0f'
        self.assertRaises(Forbidden, self._callFUT, request)

    def test_w_token_in_session_w_token_in_form_miss_wo_raises(self):
        request = _makeRequestWSession(_csrft_='deadbeef')
        request.form['csrf_token'] = 'bab3l0f'
        self.assertFalse(self._callFUT(request, raises=False))

    def test_w_token_in_session_w_token_in_form_hit(self):
        request = _makeRequestWSession(_csrft_='deadbeef')
        request.form['csrf_token'] = 'deadbeef'
        self.assertTrue(self._callFUT(request))


class CSRFTokenTests(unittest.TestCase):

    def _getTargetClass(self):
        from Products.PluggableAuthService.utils import CSRFToken
        return CSRFToken

    def _makeOne(self, context=None, request=None):
        if context is None:
            context = object()
        if request is None:
            request = _makeRequestWSession()
        return self._getTargetClass()(context, request)

    def test_wo_token_in_request(self):
        request = _makeRequestWSession()
        token = self._makeOne(request=request)
        value = token.token()
        self.assertTrue(isinstance(value, str))
        self.assertFalse(set(value) - set('0123456789abcdef'))

    def test_w_token_in_request(self):
        request = _makeRequestWSession()
        request.SESSION['_csrft_'] = 'deadbeef'
        token = self._makeOne(request=request)
        self.assertEqual(token.token(), 'deadbeef')

    def test___call___raises(self):
        from zExceptions import Forbidden
        request = _makeRequestWSession()
        request.SESSION['_csrft_'] = 'deadbeef'
        token = self._makeOne(request=request)
        self.assertRaises(Forbidden, token)


class Test_csrf_only(unittest.TestCase):

    def _callFUT(self, *args, **kw):
        from Products.PluggableAuthService.utils import csrf_only
        return csrf_only(*args, **kw)

    def test_w_function_no_REQUEST(self):
        def no_request(foo, bar, **kw):
            """I haz no REQUEST"""
        self.assertRaises(ValueError, self._callFUT, no_request)

    def test_w_function_w_positional_REQUEST(self):
        from zExceptions import Forbidden

        def w_positional_request(foo, bar, REQUEST):
            """I haz REQUEST as positional arg"""
            return 42

        wrapped = self._callFUT(w_positional_request)
        self.assertEqual(wrapped.__name__, w_positional_request.__name__)
        self.assertEqual(wrapped.__module__, w_positional_request.__module__)
        self.assertEqual(wrapped.__doc__, w_positional_request.__doc__)
        self.assertRaises(Forbidden, wrapped, foo=None, bar=None,
                          REQUEST=_makeRequestWSession())
        req = _makeRequestWSession(_csrft_='deadbeef')
        req.form['csrf_token'] = 'deadbeef'
        self.assertEqual(wrapped(foo=None, bar=None, REQUEST=req), 42)

    def test_w_function_w_optional_REQUEST(self):
        from zExceptions import Forbidden

        def w_optional_request(foo, bar, REQUEST=None):
            """I haz REQUEST as kw arg"""
            return 42

        wrapped = self._callFUT(w_optional_request)
        self.assertEqual(wrapped.__name__, w_optional_request.__name__)
        self.assertEqual(wrapped.__module__, w_optional_request.__module__)
        self.assertEqual(wrapped.__doc__, w_optional_request.__doc__)
        self.assertRaises(Forbidden, wrapped, foo=None, bar=None,
                          REQUEST=_makeRequestWSession())
        req = _makeRequestWSession(_csrft_='deadbeef')
        req.form['csrf_token'] = 'deadbeef'
        self.assertEqual(wrapped(foo=None, bar=None, REQUEST=req), 42)


def _createHashedValue(items):
    try:
        from hashlib import sha1 as sha
    except ImportError:
        from sha import new as sha

    hasher = sha()
    items = list(items)
    items.sort()
    for k, v in items:
        if isinstance(k, six.text_type):
            k = k.encode('utf-8')
        hasher.update(k)
        if isinstance(v, six.text_type):
            v = v.encode('utf-8')
        hasher.update(v)
    return hasher.hexdigest()


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(Test_createViewName),
        unittest.makeSuite(Test_createKeywords),
        unittest.makeSuite(Test_getCSRFToken),
        unittest.makeSuite(Test_checkCSRFToken),
        unittest.makeSuite(CSRFTokenTests),
        unittest.makeSuite(Test_csrf_only),
    ))
