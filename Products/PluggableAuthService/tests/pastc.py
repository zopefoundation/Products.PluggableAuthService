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
from base64 import encodestring
from Testing.ZopeTestCase import user_name
from Testing.ZopeTestCase import user_password
from Testing.ZopeTestCase import user_role
from Testing import ZopeTestCase
from Products.PluggableAuthService.interfaces import plugins as iplugins

ZopeTestCase.installProduct('PluginRegistry')
ZopeTestCase.installProduct('PluggableAuthService')
ZopeTestCase.installProduct('StandardCacheManagers')
ZopeTestCase.installProduct('GenericSetup')

user_auth = encodestring('%s:%s' % (user_name, user_password)).rstrip()


class PASTestCase(ZopeTestCase.ZopeTestCase):
    """ZopeTestCase with a PAS instead of the default user folder
    """

    def _setupUserFolder(self):
        """Creates a Pluggable Auth Service."""
        factory = self.folder.manage_addProduct['PluggableAuthService']
        factory.addPluggableAuthService()
        pas = self.folder.acl_users
        factory = pas.manage_addProduct['PluggableAuthService']
        factory.addHTTPBasicAuthHelper('http_auth')
        factory.addZODBUserManager('users')
        factory.addZODBRoleManager('roles')
        plugins = pas.plugins
        plugins.activatePlugin(iplugins.IChallengePlugin, 'http_auth')
        plugins.activatePlugin(iplugins.IExtractionPlugin, 'http_auth')
        plugins.activatePlugin(iplugins.IUserAdderPlugin, 'users')
        plugins.activatePlugin(iplugins.IAuthenticationPlugin, 'users')
        plugins.activatePlugin(iplugins.IUserEnumerationPlugin, 'users')
        plugins.activatePlugin(iplugins.IRolesPlugin, 'roles')
        plugins.activatePlugin(iplugins.IRoleAssignerPlugin, 'roles')
        plugins.activatePlugin(iplugins.IRoleEnumerationPlugin, 'roles')

    def _setupUser(self):
        """Creates the default user."""
        # OMFG, why doesn't PAS support userFolderAddUser?
        uf = self.folder.acl_users
        uf._doAddUser(user_name, user_password, [user_role], [])
