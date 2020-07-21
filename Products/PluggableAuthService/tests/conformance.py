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
""" Base classes for testing plugin interface conformance.
"""

from zope.interface.verify import verifyClass


class IExtractionPlugin_conformance:

    def test_IExtractionPlugin_conformance(self):

        from Products.PluggableAuthService.interfaces.plugins import IExtractionPlugin  # NOQA

        verifyClass(IExtractionPlugin, self._getTargetClass())

    def test_IExtractionPlugin_listInterfaces(self):

        from Products.PluggableAuthService.interfaces.plugins import IExtractionPlugin  # NOQA

        listed = self._makeOne().listInterfaces()
        self.assertTrue(IExtractionPlugin.__name__ in listed)


class ILoginPasswordHostExtractionPlugin_conformance:

    def test_ILoginPasswordHostExtractionPlugin_conformance(self):

        from Products.PluggableAuthService.interfaces.plugins import ILoginPasswordHostExtractionPlugin  # NOQA

        verifyClass(ILoginPasswordHostExtractionPlugin,
                    self._getTargetClass())

    def test_ILoginPasswordHostExtractionPlugin_listInterfaces(self):

        from Products.PluggableAuthService.interfaces.plugins import ILoginPasswordHostExtractionPlugin  # NOQA

        listed = self._makeOne().listInterfaces()
        self.assertTrue(ILoginPasswordHostExtractionPlugin.__name__ in listed)


class IChallengePlugin_conformance:

    def test_IChallengePlugin_conformance(self):

        from Products.PluggableAuthService.interfaces.plugins import IChallengePlugin  # NOQA

        verifyClass(IChallengePlugin, self._getTargetClass())

    def test_IChallengePlugin_listInterfaces(self):

        from Products.PluggableAuthService.interfaces.plugins import IChallengePlugin  # NOQA

        listed = self._makeOne().listInterfaces()
        self.assertTrue(IChallengePlugin.__name__ in listed)


class ICredentialsUpdatePlugin_conformance:

    def test_ICredentialsUpdatePlugin_conformance(self):

        from Products.PluggableAuthService.interfaces.plugins import ICredentialsUpdatePlugin  # NOQA

        verifyClass(ICredentialsUpdatePlugin, self._getTargetClass())

    def test_ICredentialsUpdatePlugin_listInterfaces(self):

        from Products.PluggableAuthService.interfaces.plugins import ICredentialsUpdatePlugin  # NOQA

        listed = self._makeOne().listInterfaces()
        self.assertTrue(ICredentialsUpdatePlugin.__name__ in listed)


class ICredentialsResetPlugin_conformance:

    def test_ICredentialsResetPlugin_conformance(self):

        from Products.PluggableAuthService.interfaces.plugins import ICredentialsResetPlugin  # NOQA

        verifyClass(ICredentialsResetPlugin, self._getTargetClass())

    def test_ICredentialsResetPlugin_listInterfaces(self):

        from Products.PluggableAuthService.interfaces.plugins import ICredentialsResetPlugin  # NOQA

        listed = self._makeOne().listInterfaces()
        self.assertTrue(ICredentialsResetPlugin.__name__ in listed)


class IAuthenticationPlugin_conformance:

    def test_AuthenticationPlugin_conformance(self):

        from Products.PluggableAuthService.interfaces.plugins import IAuthenticationPlugin  # NOQA

        verifyClass(IAuthenticationPlugin, self._getTargetClass())

    def test_IAuthenticationPlugin_listInterfaces(self):

        from Products.PluggableAuthService.interfaces.plugins import IAuthenticationPlugin  # NOQA

        listed = self._makeOne().listInterfaces()
        self.assertTrue(IAuthenticationPlugin.__name__ in listed)


class IUserEnumerationPlugin_conformance:

    def test_UserEnumerationPlugin_conformance(self):

        from Products.PluggableAuthService.interfaces.plugins import IUserEnumerationPlugin  # NOQA

        verifyClass(IUserEnumerationPlugin, self._getTargetClass())

    def test_IUserEnumerationPlugin_listInterfaces(self):

        from Products.PluggableAuthService.interfaces.plugins import IUserEnumerationPlugin  # NOQA

        listed = self._makeOne().listInterfaces()
        self.assertTrue(IUserEnumerationPlugin.__name__ in listed)


class IUserAdderPlugin_conformance:

    def test_UserAdderPlugin_conformance(self):

        from Products.PluggableAuthService.interfaces.plugins import IUserAdderPlugin  # NOQA

        verifyClass(IUserAdderPlugin, self._getTargetClass())

    def test_IUserAdderPlugin_listInterfaces(self):

        from Products.PluggableAuthService.interfaces.plugins import IUserAdderPlugin  # NOQA

        listed = self._makeOne().listInterfaces()
        self.assertTrue(IUserAdderPlugin.__name__ in listed)


class IGroupEnumerationPlugin_conformance:

    def test_GroupEnumerationPlugin_conformance(self):

        from Products.PluggableAuthService.interfaces.plugins import IGroupEnumerationPlugin  # NOQA

        verifyClass(IGroupEnumerationPlugin, self._getTargetClass())

    def test_IGroupEnumerationPlugin_listInterfaces(self):

        from Products.PluggableAuthService.interfaces.plugins import IGroupEnumerationPlugin  # NOQA

        listed = self._makeOne().listInterfaces()
        self.assertTrue(IGroupEnumerationPlugin.__name__ in listed)


class IGroupsPlugin_conformance:

    def test_GroupsPlugin_conformance(self):

        from Products.PluggableAuthService.interfaces.plugins import IGroupsPlugin  # NOQA

        verifyClass(IGroupsPlugin, self._getTargetClass())

    def test_IGroupsPlugin_listInterfaces(self):

        from Products.PluggableAuthService.interfaces.plugins import IGroupsPlugin  # NOQA

        listed = self._makeOne().listInterfaces()
        self.assertTrue(IGroupsPlugin.__name__ in listed)


class IRoleEnumerationPlugin_conformance:

    def test_RoleEnumerationPlugin_conformance(self):

        from Products.PluggableAuthService.interfaces.plugins import IRoleEnumerationPlugin  # NOQA

        verifyClass(IRoleEnumerationPlugin, self._getTargetClass())

    def test_IRoleEnumerationPlugin_listInterfaces(self):

        from Products.PluggableAuthService.interfaces.plugins import IRoleEnumerationPlugin  # NOQA

        listed = self._makeOne().listInterfaces()
        self.assertTrue(IRoleEnumerationPlugin.__name__ in listed)


class IRolesPlugin_conformance:

    def test_RolesPlugin_conformance(self):

        from Products.PluggableAuthService.interfaces.plugins import IRolesPlugin  # NOQA

        verifyClass(IRolesPlugin, self._getTargetClass())

    def test_IRolesPlugin_listInterfaces(self):

        from Products.PluggableAuthService.interfaces.plugins import IRolesPlugin  # NOQA

        listed = self._makeOne().listInterfaces()
        self.assertTrue(IRolesPlugin.__name__ in listed)


class IRoleAssignerPlugin_conformance:

    def test_RoleAssignerPlugin_conformance(self):

        from Products.PluggableAuthService.interfaces.plugins import IRoleAssignerPlugin  # NOQA

        verifyClass(IRoleAssignerPlugin, self._getTargetClass())

    def test_IRoleAssignerPlugin_listInterfaces(self):

        from Products.PluggableAuthService.interfaces.plugins import IRoleAssignerPlugin  # NOQA

        listed = self._makeOne().listInterfaces()
        self.assertTrue(IRoleAssignerPlugin.__name__ in listed)


class IChallengeProtocolChooser_conformance:

    def test_ChallengeProtocolChooser_conformance(self):

        from Products.PluggableAuthService.interfaces.plugins import IChallengeProtocolChooser  # NOQA

        verifyClass(IChallengeProtocolChooser, self._getTargetClass())

    def test_IChallengeProtocolChooser_listInterfaces(self):

        from Products.PluggableAuthService.interfaces.plugins import IChallengeProtocolChooser  # NOQA

        listed = self._makeOne().listInterfaces()
        self.assertTrue(IChallengeProtocolChooser.__name__ in listed)


class IRequestTypeSniffer_conformance:

    def test_RequestTypeSniffer_conformance(self):

        from Products.PluggableAuthService.interfaces.plugins import IRequestTypeSniffer  # NOQA

        verifyClass(IRequestTypeSniffer, self._getTargetClass())

    def test_IRequestTypeSniffer_listInterfaces(self):

        from Products.PluggableAuthService.interfaces.plugins import IRequestTypeSniffer  # NOQA

        listed = self._makeOne().listInterfaces()
        self.assertTrue(IRequestTypeSniffer.__name__ in listed)


class IUserFolder_conformance:

    def test_conformance_IUserFolder(self):

        from Products.PluggableAuthService.interfaces.authservice import IUserFolder  # NOQA

        verifyClass(IUserFolder, self._getTargetClass())


class IBasicUser_conformance:

    def test_conformance_IBasicUser(self):

        from Products.PluggableAuthService.interfaces.authservice import IBasicUser  # NOQA

        verifyClass(IBasicUser, self._getTargetClass())


class IPropertiedUser_conformance:

    def test_conformance_IPropertiedUser(self):

        from Products.PluggableAuthService.interfaces.authservice import IPropertiedUser  # NOQA

        verifyClass(IPropertiedUser, self._getTargetClass())


class IPropertySheet_conformance:

    def test_conformance_IPropertySheet(self):

        from Products.PluggableAuthService.interfaces.propertysheets import IPropertySheet  # NOQA

        verifyClass(IPropertySheet, self._getTargetClass())


class INotCompetentPlugin_conformance:

    def test_INotCompetentPlugin_conformance(self):

        from Products.PluggableAuthService.interfaces.plugins import INotCompetentPlugin  # NOQA

        verifyClass(INotCompetentPlugin, self._getTargetClass())

    def test_INotCompetentPlugin_listInterfaces(self):

        from Products.PluggableAuthService.interfaces.plugins import INotCompetentPlugin  # NOQA

        listed = self._makeOne().listInterfaces()
        self.assertTrue(INotCompetentPlugin.__name__ in listed)
