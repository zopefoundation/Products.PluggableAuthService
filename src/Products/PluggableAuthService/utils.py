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
import binascii
import functools
import inspect
import logging
import os
from hashlib import sha1

import six
from six.moves.urllib.parse import urlparse
from six.moves.urllib.parse import urlunparse

from AccessControl import ClassSecurityInfo
# BBB import
from AccessControl.requestmethod import postonly  # noqa
from App.Common import package_home
from zExceptions import Forbidden
from zope import interface
from zope.publisher.interfaces.browser import IBrowserRequest  # noqa


logger = logging.getLogger('PluggableAuthService')


def directlyProvides(obj, *interfaces):
    normalized_interfaces = []
    for i in interfaces:
        normalized_interfaces.append(i)
    return interface.directlyProvides(obj,  # NOQA: D001
                                      *normalized_interfaces)


def classImplements(class_, *interfaces):
    normalized_interfaces = []
    for i in interfaces:
        normalized_interfaces.append(i)
    return interface.classImplements(class_,  # NOQA: D001
                                     *normalized_interfaces)


product_dir = package_home(globals())
product_prefix = os.path.split(product_dir)[0]
_wwwdir = os.path.join(product_dir, 'www')


def makestr(s):
    """Converts 's' to a non-Unicode string"""
    if isinstance(s, six.binary_type):
        return s
    if not isinstance(s, six.text_type):
        s = repr(s)
    if isinstance(s, six.text_type):
        s = s.encode('utf-8')
    return s


def createViewName(method_name, user_handle=None):
    """
        Centralized place for creating the "View Name" that identifies
        a ZCacheable record in a RAMCacheManager
    """
    if not user_handle:
        return makestr(method_name)
    else:
        return b'%s-%s' % (makestr(method_name), makestr(user_handle))


def createKeywords(**kw):
    """
        Centralized place for creating the keywords that identify
        a ZCacheable record in a RAMCacheManager.

        Keywords are hashed so we don't accidentally expose sensitive
        information.
    """
    keywords = sha1()
    for k, v in sorted(kw.items()):
        keywords.update(makestr(k))
        keywords.update(makestr(v))

    return {'keywords': keywords.hexdigest()}


def getCSRFToken(request):
    session = getattr(request, 'SESSION', None)
    if session is not None:
        token = session.get('_csrft_', None)
        if token is None:
            token = session['_csrft_'] = binascii.hexlify(os.urandom(20))
    else:
        # Can happen in tests.
        token = binascii.hexlify(os.urandom(20))
    if six.PY3 and isinstance(token, bytes):
        token = token.decode('utf8')
    return token


def checkCSRFToken(request, token='csrf_token', raises=True):
    """ Check CSRF token in session against token formdata.

    If the values don't match, and 'raises' is True, raise a Forbidden.

    If the values don't match, and 'raises' is False, return False.

    If the values match, return True.
    """
    if getattr(request, 'SESSION', None) is None:
        # Sessioning is not available at all, just give up
        logger.warning(
            'Built-in CSRF check disabled - sessioning not available')
        return True

    if request.form.get(token) != getCSRFToken(request):
        if raises:
            raise Forbidden('incorrect CSRF token')
        return False
    return True


class CSRFToken(object):
    # View helper for rendering CSRF token in templates.
    #
    # E.g., in every protected form, add this::
    #
    #   <input type="hidden" name="csrf_token"
    #          tal:attributes="value context/@@csrf_token" />

    security = ClassSecurityInfo()
    security.declareObjectPublic()

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        raise Forbidden()

    def token(self):
        # API for template use
        return getCSRFToken(self.request)


def csrf_only(wrapped):
    try:
        wrapped_spec = inspect.getfullargspec(wrapped)
    except AttributeError:  # Python 2
        wrapped_spec = inspect.getargspec(wrapped)
    args, varargs, kwargs, defaults = wrapped_spec[:4]
    if 'REQUEST' not in args:
        raise ValueError("Method doesn't name request")
    r_index = args.index('REQUEST')

    arglen = len(args)
    if defaults is not None:
        defaults = list(zip(args[arglen - len(defaults):], defaults))
        arglen -= len(defaults)

    spec = (args, varargs, kwargs, defaults)
    try:
        signature = inspect.signature(wrapped)
        new_parameters = []
        for param in signature.parameters.values():
            if param.default is not inspect.Parameter.empty:
                param = param.replace(default=None)
            new_parameters.append(param)
        argspec = str(signature.replace(parameters=new_parameters))
    except AttributeError:  # Python 2
        argspec = inspect.formatargspec(formatvalue=lambda v: '=None', *spec)
    lines = ['def wrapper' + argspec + ':',
             '    if IBrowserRequest.providedBy(REQUEST):',
             '        checkCSRFToken(REQUEST)',
             '    return wrapped(' + ','.join(args) + ')',
             ]
    g = globals().copy()
    l_copy = locals().copy()
    g['wrapped'] = wrapped
    exec('\n'.join(lines), g, l_copy)

    return functools.wraps(wrapped)(l_copy['wrapper'])


def url_local(url):
    """Helper to convert a URL into a site-local URL

    This function removes the protocol and host parts of a URL in order to
    prevent open redirect issues.
    """
    if url:
        parsed = urlparse(url)
        url = urlunparse(('', '') + parsed[2:])
    return url
