# -*- coding: utf-8 -*-
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
from AccessControl import ClassSecurityInfo
from App.Common import package_home
from hashlib import sha1 as sha
from zope import interface
from zope.deprecation import deprecation
from ZPublisher import Forbidden
import binascii
import functools
import inspect
import os

# special import for inline code wrapper, its used!
from zope.publisher.interfaces.browser import IBrowserRequest  # noqa

# BBB import
from AccessControl.requestmethod import postonly
postonly = deprecation.DeprecatedMethod(
    postonly,
    "import postonly from AccessControl.requestmethod"
)


@deprecation.deprecate(
    "Use directlyProvides from zope.interface directly"
)
def directlyProvides(obj, *interfaces):
    normalized_interfaces = []
    for i in interfaces:
        normalized_interfaces.append(i)
    return interface.directlyProvides(obj, *normalized_interfaces)


@deprecation.deprecate(
    "Use implementer decorator from zope.interface directly"
)
def classImplements(class_, *interfaces):
    normalized_interfaces = []
    for i in interfaces:
        normalized_interfaces.append(i)
    return interface.classImplements(class_, *normalized_interfaces)


product_dir = package_home(globals())
product_prefix = os.path.split(product_dir)[0]

_wwwdir = os.path.join(product_dir, 'www')

#
#   Most of this module is shamelessly ripped off from Zope3.test
#


def remove_stale_bytecode(arg, dirname, names):
    """
        Troll product, removing compiled turds whose source is now gone.
    """
    names = map(os.path.normcase, names)
    for name in names:
        if name.endswith(".pyc") or name.endswith(".pyo"):
            srcname = name[:-1]
            if srcname not in names:
                fullname = os.path.join(dirname, name)
                if __debug__:
                    print "Removing stale bytecode file", fullname
                os.unlink(fullname)


class TestFileFinder:

    def __init__(self):
        self.files = []

    def visit(self, prefix, dir, files):
        """
            Visitor for os.path.walk:  accumulates filenamse of unittests.
        """
        # if dir[-5:] != "tests":
        #    return

        # ignore tests that aren't in packages
        if "__init__.py" not in files:
            if not files or files == ['CVS']:
                return
            if 0 and __debug__:  # XXX: don't care!
                print "not a package", dir
            return

        for file in files:

            if file.startswith(prefix) and file.endswith(".py"):
                path = os.path.join(dir, file)
                self.files.append(path)


def find_unit_test_files(from_dir=product_dir, test_prefix='test'):
    """
        Walk the product, return a list of all unittest files.
    """
    finder = TestFileFinder()
    os.path.walk(from_dir, finder.visit, test_prefix)
    return finder.files


def module_name_from_path(path):
    """
        Return the dotted module name matching the filesystem path.
    """
    assert path.endswith('.py')
    path = path[:-3]
    path = path[len(product_prefix) + 1:]  # strip extraneous crap
    dirs = []
    while path:
        path, end = os.path.split(path)
        dirs.insert(0, end)
    return ".".join(dirs)


def get_suite(file):
    """
        Retrieve a TestSuite from 'file'.
    """
    import unittest
    module_name = module_name_from_path(file)
    loader = unittest.defaultTestLoader
    try:
        suite = loader.loadTestsFromName('%s.test_suite' % module_name)
    except AttributeError:

        try:
            suite = loader.loadTestsFromName(module_name)
        except ImportError, err:
            print "Error importing %s\n%s" % (module_name, err)
            raise
    return suite


def allTests(from_dir=product_dir, test_prefix='test'):
    """
        Walk the product and build a unittest.TestSuite aggregating tests.
    """
    import unittest
    os.path.walk(from_dir, remove_stale_bytecode, None)
    test_files = find_unit_test_files(from_dir, test_prefix)
    test_files.sort()

    suite = unittest.TestSuite()

    for test_file in test_files:

        s = get_suite(test_file)
        if s is not None:
            suite.addTest(s)

    return suite


def makestr(s):
    """Converts 's' to a non-Unicode string"""
    if isinstance(s, unicode):
        s = s.encode('utf-8')
    return str(s)


def createViewName(method_name, user_handle=None):
    """
        Centralized place for creating the "View Name" that identifies
        a ZCacheable record in a RAMCacheManager
    """
    if not user_handle:
        return makestr(method_name)
    else:
        return '%s-%s' % (makestr(method_name), makestr(user_handle))


def createKeywords(**kw):
    """
        Centralized place for creating the keywords that identify
        a ZCacheable record in a RAMCacheManager.

        Keywords are hashed so we don't accidentally expose sensitive
        information.
    """
    keywords = sha()

    items = kw.items()
    items.sort()
    for k, v in items:
        keywords.update(makestr(k))
        keywords.update(makestr(v))

    return {'keywords': keywords.hexdigest()}


def getCSRFToken(request):
    session = getattr(request, 'SESSION', None)
    if not session:
        # Can happen in tests.
        return binascii.hexlify(os.urandom(20))
    token = session.get('_csrft_', None)
    if token is None:
        token = session['_csrft_'] = binascii.hexlify(os.urandom(20))
    return token


def checkCSRFToken(request, token='csrf_token', raises=True):
    """ Check CSRF token in session against token formdata.

    If the values don't match, and 'raises' is True, raise a Forbidden.

    If the values don't match, and 'raises' is False, return False.

    If the values match, return True.
    """
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
    args, varargs, kwargs, defaults = inspect.getargspec(wrapped)
    if 'REQUEST' not in args:
        raise ValueError("Method doesn't name request")
    r_index = args.index('REQUEST')

    arglen = len(args)
    if defaults is not None:
        defaults = zip(args[arglen - len(defaults):], defaults)
        arglen -= len(defaults)

    spec = (args, varargs, kwargs, defaults)
    argspec = inspect.formatargspec(formatvalue=lambda v: '=None', *spec)
    callargs = inspect.formatargspec(formatvalue=lambda v: '', *spec)
    lines = ['def wrapper' + argspec + ':',
             '    if IBrowserRequest.providedBy(REQUEST):',
             '        checkCSRFToken(REQUEST)',
             '    return wrapped(' + ','.join(args) + ')',
             ]
    g = globals().copy()
    l = locals().copy()
    g['wrapped'] = wrapped
    exec '\n'.join(lines) in g, l

    return functools.wraps(wrapped)(l['wrapper'])
