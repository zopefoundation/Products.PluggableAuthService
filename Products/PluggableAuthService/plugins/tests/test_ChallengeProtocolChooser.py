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
"""Unit tests for ChallengeProtocolChooser."""
import io
import unittest

import six

import Testing.ZopeTestCase

from Products.PluggableAuthService import HAVE_ZSERVER
from Products.PluggableAuthService.tests.conformance import \
    IChallengeProtocolChooser_conformance


XMLRPC_CALL = b"""\
<?xml version="1.0"?>
<methodCall>
    <methodName>test_script</methodName>
</methodCall>"""

if six.PY2:
    XML_PREAMBLE = b"<?xml version='1.0'?>"
else:
    XML_PREAMBLE = b'<?xml version="1.0" encoding="utf-8" ?>'

XMLRPC_ACCESS_GRANTED = b"""\
%s
<methodResponse>
<params>
<param>
<value><string>Access Granted</string></value>
</param>
</params>
</methodResponse>
""" % XML_PREAMBLE


class ChallengeProtocolChooser(unittest.TestCase,
                               IChallengeProtocolChooser_conformance):

    def _getTargetClass(self):
        from Products.PluggableAuthService.plugins.ChallengeProtocolChooser \
            import ChallengeProtocolChooser

        return ChallengeProtocolChooser

    def _makeOne(self, id='test', *args, **kw):
        return self._getTargetClass()(id, *args, **kw)


class ChallengeProtocolChooserTestHelper(object):
    """Helper functions for the ChallengeProtocolChooser tests."""

    def setup_user_folder(self):
        # Let's start by setting up a PAS instance inside our existing test
        # folder.
        folder = self.folder
        self.assertIn('acl_users', folder.objectIds())
        folder.manage_delObjects(ids=['acl_users'])
        self.assertNotIn('acl_users', folder.objectIds())

        dispatcher = folder.manage_addProduct['PluggableAuthService']
        dispatcher.addPluggableAuthService()

        self.assertIn('acl_users', folder.objectIds())
        self.assertEqual(folder.acl_users.meta_type, 'Pluggable Auth Service')

        # Now, we'll setup this PAS instance with what most people would get by
        # default, users and roles stored in ZODB with HTTP Basic auth.
        pas = folder.acl_users
        dispatcher = pas.manage_addProduct['PluggableAuthService']

        dispatcher.addZODBUserManager('users')
        dispatcher.addZODBRoleManager('roles')
        dispatcher.addHTTPBasicAuthHelper('http_auth')

        plugins = pas.plugins

        from Products.PluggableAuthService.interfaces.plugins import \
            IAuthenticationPlugin, IUserEnumerationPlugin, IRolesPlugin, \
            IRoleEnumerationPlugin, IRoleAssignerPlugin, IUserAdderPlugin

        plugins.activatePlugin(IUserAdderPlugin, 'users')
        plugins.activatePlugin(IAuthenticationPlugin, 'users')
        plugins.activatePlugin(IUserEnumerationPlugin, 'users')
        plugins.activatePlugin(IRolesPlugin, 'roles')
        plugins.activatePlugin(IRoleEnumerationPlugin, 'roles')
        plugins.activatePlugin(IRoleAssignerPlugin, 'roles')

    def setup_http_auth(self):
        from Products.PluggableAuthService.interfaces.plugins import \
            IChallengePlugin, IExtractionPlugin

        plugins = self.folder.acl_users.plugins
        plugins.activatePlugin(IExtractionPlugin, 'http_auth')
        plugins.activatePlugin(IChallengePlugin, 'http_auth')

    def setup_cookie_auth(self):
        # Adding a Cookie Auth Helper to test the correct behaviour of the
        # Challenge Protocol Helper.
        from Products.PluggableAuthService.interfaces.plugins import \
            IChallengePlugin, IExtractionPlugin
        dispatcher = self.folder.acl_users.manage_addProduct[
            'PluggableAuthService']
        dispatcher.addCookieAuthHelper('cookie_auth', cookie_name='__ac')

        plugins = self.folder.acl_users.plugins
        plugins.activatePlugin(IExtractionPlugin, 'cookie_auth')
        plugins.activatePlugin(IChallengePlugin, 'cookie_auth')

    def setup_sniffer(self):
        from Products.PluggableAuthService.interfaces.plugins import \
            IRequestTypeSniffer, IChallengeProtocolChooser

        dispatcher = self.folder.acl_users.manage_addProduct[
            'PluggableAuthService']
        dispatcher.addRequestTypeSnifferPlugin('sniffer')
        plugins = self.folder.acl_users.plugins
        plugins.activatePlugin(IRequestTypeSniffer, 'sniffer')

        mapping = {'WebDAV': ['http'],
                   'XML-RPC': ['http'],
                   'Browser': []}

        dispatcher.addChallengeProtocolChooserPlugin(
            'chooser', mapping=mapping)
        plugins.activatePlugin(IChallengeProtocolChooser, 'chooser')

    def setup_user(self):
        # Create a user for testing:

        from Products.PluggableAuthService.PropertiedUser import PropertiedUser
        pas = self.folder.acl_users
        self.assertIsNone(pas.getUserById('test_user_'))

        username, password = 'test_user_', 'test_user_pw'
        self.basic_auth = '%s:%s' % (username, password)
        user = pas._doAddUser(username, password, ['Manager'], [])
        self.assertIsInstance(user, PropertiedUser)
        self.assertIsNotNone(pas.getUserById('test_user_'))

    def setup_database(self):
        # We are now going to try some different kinds of requests and make
        # sure all of them work. They all use HTTP Basic Auth, which is the
        # default in this configuration we just set up. For the sake of
        # testing, we are going to create a simple script that requires the
        # 'Manager' role to be called.
        self.folder_name = self.folder.getId()
        dispatcher = self.folder.manage_addProduct['DocumentTemplate']
        dispatcher.manage_addDTMLMethod('test_script')

        script = self.folder._getOb('test_script')
        script.munge('Access Granted')
        script.manage_permission(permission_to_manage='View',
                                 roles=['Manager'], acquire=0)

    def assertStatus(self, response, status):
        self.assertEqual(status, response.getOutput().split(b'\r\n')[0])


class ChallengeProtocolChooserBasicAuthTests(
        Testing.ZopeTestCase.Functional,
        Testing.ZopeTestCase.ZopeTestCase,
        ChallengeProtocolChooserTestHelper):
    """Testing of basic auth capabilities of `ChallengeProtocolChooser`.

    The Challenge Protocol Chooser is a plugin that decides what
    authentication protocol to use for a given request type.
    """

    def setUp(self):
        super(ChallengeProtocolChooserBasicAuthTests, self).setUp()
        self.setup_user_folder()
        self.setup_http_auth()
        self.setup_user()
        self.setup_database()

    def test_GET_unauthorized(self):
        # Access the script through a simple ``GET`` request, simulating
        # browser access. Anonymous user should be challenged with a 401
        # response status.

        response = self.publish('/{0.folder_name}/test_script'.format(self))
        self.assertStatus(response, b'HTTP/1.1 401 Unauthorized')

    def test_GET_authorized(self):
        # With the right credentials though the request should succeed:
        response = self.publish(
            '/{0.folder_name}/test_script'.format(self), basic=self.basic_auth)
        self.assertStatus(response, b'HTTP/1.1 200 OK')
        self.assertIn('Access Granted', str(response))

    @unittest.skipIf(not HAVE_ZSERVER, 'WebDAV requires ZServer')
    def test_WebDAV_unauthorized(self):
        # Now a PROPFIND request, simulating a WebDAV client. Anonymous user
        # should be challenged with a 401 response status:
        response = self.publish('/{0.folder_name}/test_script'.format(self),
                                request_method='PROPFIND')
        self.assertStatus(response, b'HTTP/1.1 401 Unauthorized')

        response = self.publish(
            '/{0.folder_name}/test_script/manage_DAVget'.format(self),
            request_method='GET')
        self.assertStatus(response, b'HTTP/1.1 401 Unauthorized')

    @unittest.skipIf(not HAVE_ZSERVER, 'WebDAV requires ZServer')
    def test_WebDAV_authorized(self):
        # And with the right credentials the request should succeed:
        response = self.publish('/{0.folder_name}/test_script'.format(self),
                                request_method='PROPFIND',
                                basic=self.basic_auth)
        self.assertStatus(response, b'HTTP/1.1 207 Multi-Status')

        response = self.publish(
            '/{0.folder_name}/test_script/manage_DAVget'.format(self),
            request_method='GET', basic=self.basic_auth)
        self.assertStatus(response, b'HTTP/1.1 200 OK')

    def test_XMLRPC_unauthorized(self):
        # And a XML-RPC Request. Again, Anonymous user should be challenged
        # with a 401 response status.
        response = self.publish(
            '/{0.folder_name}'.format(self), request_method='POST',
            env={'CONTENT_TYPE': 'text/xml; charset="utf-8"'},
            stdin=io.BytesIO(XMLRPC_CALL))
        self.assertStatus(response, b'HTTP/1.1 401 Unauthorized')

    def test_XMLRPC_authorized(self):
        # And with valid credentials the reqeuest should succeed:
        response = self.publish(
            '/{0.folder_name}'.format(self), request_method='POST',
            env={'CONTENT_TYPE': 'text/xml; charset="utf-8"'},
            stdin=io.BytesIO(XMLRPC_CALL), basic=self.basic_auth)
        self.assertStatus(response, b'HTTP/1.1 200 OK')
        self.assertEqual(
            response.getHeader('Content-Type'), 'text/xml; charset=utf-8')
        self.assertEqual(XMLRPC_ACCESS_GRANTED, response.getBody())


class ChallengeProtocolChooserCookieAuthTests(
        Testing.ZopeTestCase.Functional,
        Testing.ZopeTestCase.ZopeTestCase,
        ChallengeProtocolChooserTestHelper):
    """Testing of cookie auth capabilities of `ChallengeProtocolChooser`."""

    def setUp(self):
        super(ChallengeProtocolChooserCookieAuthTests, self).setUp()
        self.setup_user_folder()
        self.setup_cookie_auth()
        self.setup_http_auth()  # HTTP Auth should appear after Cookie Auth
        self.setup_user()
        self.setup_database()

    def test_GET_unauthorized(self):
        # Now, invalid credentials should result in a 302 response status for a
        # normal (eg: browser) request:
        response = self.publish('/{0.folder_name}/test_script'.format(self))
        self.assertStatus(response, b'HTTP/1.1 302 Found')

    @unittest.skipIf(not HAVE_ZSERVER, 'WebDAV requires ZServer')
    def test_WebDAV_unauthorized(self):
        # And the same for a WebDAV request:
        response = self.publish('/{0.folder_name}/test_script'.format(self),
                                request_method='PROPFIND')
        self.assertStatus(response, b'HTTP/1.1 302 Found')

        response = self.publish(
            '/{0.folder_name}/test_script/manage_DAVget'.format(self),
            request_method='GET')
        self.assertStatus(response, b'HTTP/1.1 302 Found')

    def test_XMLRPC_unauthorized(self):
        # And for a XML-RPC request:
        response = self.publish(
            '/{0.folder_name}'.format(self), request_method='POST',
            env={'CONTENT_TYPE': 'text/xml; charset="utf-8"'},
            stdin=io.BytesIO(XMLRPC_CALL))
        self.assertStatus(response, b'HTTP/1.1 302 Found')


class ChallengeProtocolChooserCookieAuthTypeSnifferTests(
        Testing.ZopeTestCase.Functional,
        Testing.ZopeTestCase.ZopeTestCase,
        ChallengeProtocolChooserTestHelper):
    """Testing of cookie auth + type sniffer at `ChallengeProtocolChooser`.

    Not all WebDAV and XML-RPC clients understand the redirect. Even worse,
    they will not be able to display the login form that is the target of this
    redirect.

    For this reason we should disable the Cookie Auth Helper for non-browser
    requests. In fact, we might only want plugins that understand the 'http'
    authorization protocol to issue challenges for WebDAV and XML-RPC.

    To do this, we use the Challenge Protocol Chooser plugin together with the
    Request Type Sniffer plugin.
    """

    def setUp(self):
        super(ChallengeProtocolChooserCookieAuthTypeSnifferTests, self).setUp()
        self.setup_user_folder()
        self.setup_cookie_auth()
        self.setup_http_auth()  # HTTP Auth should appear after Cookie Auth
        self.setup_sniffer()
        self.setup_user()
        self.setup_database()

    def test_GET_unauthorized(self):
        # Now, invalid credentials should result in a 302 response status for a
        # normal (eg: browser) request:
        response = self.publish('/{0.folder_name}/test_script'.format(self))
        self.assertStatus(response, b'HTTP/1.1 302 Found')

    @unittest.skipIf(not HAVE_ZSERVER, 'WebDAV requires ZServer')
    def test_WebDAV_unauthorized(self):
        # A WebDAV request should result in a 401 response status:
        response = self.publish('/{0.folder_name}/test_script'.format(self),
                                request_method='PROPFIND')
        self.assertStatus(response, b'HTTP/1.1 401 Unauthorized')

        response = self.publish(
            '/{0.folder_name}/test_script/manage_DAVget'.format(self),
            request_method='GET')
        self.assertStatus(response, b'HTTP/1.1 401 Unauthorized')

    def test_XMLRPC_unauthorized(self):
        # And a XML-RPC request should also result in a 401 response status:
        response = self.publish(
            '/{0.folder_name}'.format(self), request_method='POST',
            env={'CONTENT_TYPE': 'text/xml; charset="utf-8"'},
            stdin=io.BytesIO(XMLRPC_CALL))
        self.assertStatus(response, b'HTTP/1.1 401 Unauthorized')
