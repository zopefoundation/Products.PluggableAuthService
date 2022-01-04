##############################################################################
#
# Copyright (c) 2022 Zope Foundation and Contributors
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

from Testing.ZopeTestCase import ZopeTestCase
from zope.interface import directlyProvides

from ..interfaces.plugins import ICredentialsResetPlugin
from ..interfaces.plugins import ICredentialsUpdatePlugin
from ..interfaces.plugins import IExtractionPlugin
from .pastc import PASTestCase
from .pastc import user_name
from .pastc import user_password
from .test_PluggableAuthService import DummyCredentialsStore


class PasMixin(object):
    def _setupUserFolder(self):
        super(PasMixin, self)._setupUserFolder()
        pas = self.folder.acl_users
        plugins = pas.plugins
        creds_store = DummyCredentialsStore('creds')
        directlyProvides(creds_store, IExtractionPlugin,
                         ICredentialsUpdatePlugin, ICredentialsResetPlugin)
        pas._setObject('creds', creds_store)
        plugins.deactivatePlugin(IExtractionPlugin, 'http_auth')
        plugins.activatePlugin(IExtractionPlugin, 'creds')
        plugins.activatePlugin(ICredentialsUpdatePlugin, 'creds')
        plugins.activatePlugin(ICredentialsResetPlugin, 'creds')
        request = self.folder.REQUEST
        request["login"] = user_name
        creds_store.updateCredentials(
            request, request.response, user_name, user_password)

    def verify_logout(self):
        folder = self.folder
        request = folder.REQUEST
        return not folder.acl_users.creds.extractCredentials(request)


class ZopeMixin(object):
    def verify_logout(self):
        response = self.folder.REQUEST.response
        return response.getStatus() == 401


class Tests(object):
    def test_logout(self):
        folder = self.folder
        request = folder.REQUEST
        folder.manage_zmi_logout(request, request.response)
        self.assertTrue(self.verify_logout())


class PasLogoutTests(PasMixin, Tests, PASTestCase):
    def test_not_logged_in(self):
        from AccessControl.SecurityManagement import noSecurityManager
        noSecurityManager()
        folder = self.folder
        request = folder.REQUEST
        self.assertEqual(
            folder.manage_zmi_logout(request, request.response),
            "You are not/no longer logged in")


class ZopeLogoutTests(ZopeMixin, Tests, ZopeTestCase):
    pass
