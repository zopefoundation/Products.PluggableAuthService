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

        from ..interfaces.plugins import IExtractionPlugin

        verifyClass(IExtractionPlugin, self._getTargetClass())

    def test_IExtractionPlugin_listInterfaces(self):

        from ..interfaces.plugins import IExtractionPlugin

        listed = self._makeOne().listInterfaces()
        self.assertIn(IExtractionPlugin.__name__, listed)


class ILoginPasswordHostExtractionPlugin_conformance:

    def test_ILoginPasswordHostExtractionPlugin_conformance(self):

        from ..interfaces.plugins import ILoginPasswordHostExtractionPlugin

        verifyClass(ILoginPasswordHostExtractionPlugin,
                    self._getTargetClass())

    def test_ILoginPasswordHostExtractionPlugin_listInterfaces(self):

        from ..interfaces.plugins import ILoginPasswordHostExtractionPlugin

        listed = self._makeOne().listInterfaces()
        self.assertIn(ILoginPasswordHostExtractionPlugin.__name__, listed)


class IChallengePlugin_conformance:

    def test_IChallengePlugin_conformance(self):

        from ..interfaces.plugins import IChallengePlugin

        verifyClass(IChallengePlugin, self._getTargetClass())

    def test_IChallengePlugin_listInterfaces(self):

        from ..interfaces.plugins import IChallengePlugin

        listed = self._makeOne().listInterfaces()
        self.assertIn(IChallengePlugin.__name__, listed)


class ICredentialsUpdatePlugin_conformance:

    def test_ICredentialsUpdatePlugin_conformance(self):

        from ..interfaces.plugins import ICredentialsUpdatePlugin

        verifyClass(ICredentialsUpdatePlugin, self._getTargetClass())

    def test_ICredentialsUpdatePlugin_listInterfaces(self):

        from ..interfaces.plugins import ICredentialsUpdatePlugin

        listed = self._makeOne().listInterfaces()
        self.assertIn(ICredentialsUpdatePlugin.__name__, listed)


class ICredentialsResetPlugin_conformance:

    def test_ICredentialsResetPlugin_conformance(self):

        from ..interfaces.plugins import ICredentialsResetPlugin

        verifyClass(ICredentialsResetPlugin, self._getTargetClass())

    def test_ICredentialsResetPlugin_listInterfaces(self):

        from ..interfaces.plugins import ICredentialsResetPlugin

        listed = self._makeOne().listInterfaces()
        self.assertIn(ICredentialsResetPlugin.__name__, listed)


class IAuthenticationPlugin_conformance:

    def test_AuthenticationPlugin_conformance(self):

        from ..interfaces.plugins import IAuthenticationPlugin

        verifyClass(IAuthenticationPlugin, self._getTargetClass())

    def test_IAuthenticationPlugin_listInterfaces(self):

        from ..interfaces.plugins import IAuthenticationPlugin

        listed = self._makeOne().listInterfaces()
        self.assertIn(IAuthenticationPlugin.__name__, listed)


class IUserEnumerationPlugin_conformance:

    def test_UserEnumerationPlugin_conformance(self):

        from ..interfaces.plugins import IUserEnumerationPlugin

        verifyClass(IUserEnumerationPlugin, self._getTargetClass())

    def test_IUserEnumerationPlugin_listInterfaces(self):

        from ..interfaces.plugins import IUserEnumerationPlugin

        listed = self._makeOne().listInterfaces()
        self.assertIn(IUserEnumerationPlugin.__name__, listed)


class IUserAdderPlugin_conformance:

    def test_UserAdderPlugin_conformance(self):

        from ..interfaces.plugins import IUserAdderPlugin

        verifyClass(IUserAdderPlugin, self._getTargetClass())

    def test_IUserAdderPlugin_listInterfaces(self):

        from ..interfaces.plugins import IUserAdderPlugin

        listed = self._makeOne().listInterfaces()
        self.assertIn(IUserAdderPlugin.__name__, listed)


class IGroupEnumerationPlugin_conformance:

    def test_GroupEnumerationPlugin_conformance(self):

        from ..interfaces.plugins import IGroupEnumerationPlugin

        verifyClass(IGroupEnumerationPlugin, self._getTargetClass())

    def test_IGroupEnumerationPlugin_listInterfaces(self):

        from ..interfaces.plugins import IGroupEnumerationPlugin

        listed = self._makeOne().listInterfaces()
        self.assertIn(IGroupEnumerationPlugin.__name__, listed)


class IGroupsPlugin_conformance:

    def test_GroupsPlugin_conformance(self):

        from ..interfaces.plugins import IGroupsPlugin

        verifyClass(IGroupsPlugin, self._getTargetClass())

    def test_IGroupsPlugin_listInterfaces(self):

        from ..interfaces.plugins import IGroupsPlugin

        listed = self._makeOne().listInterfaces()
        self.assertIn(IGroupsPlugin.__name__, listed)


class IRoleEnumerationPlugin_conformance:

    def test_RoleEnumerationPlugin_conformance(self):

        from ..interfaces.plugins import IRoleEnumerationPlugin

        verifyClass(IRoleEnumerationPlugin, self._getTargetClass())

    def test_IRoleEnumerationPlugin_listInterfaces(self):

        from ..interfaces.plugins import IRoleEnumerationPlugin

        listed = self._makeOne().listInterfaces()
        self.assertIn(IRoleEnumerationPlugin.__name__, listed)


class IRolesPlugin_conformance:

    def test_RolesPlugin_conformance(self):

        from ..interfaces.plugins import IRolesPlugin

        verifyClass(IRolesPlugin, self._getTargetClass())

    def test_IRolesPlugin_listInterfaces(self):

        from ..interfaces.plugins import IRolesPlugin

        listed = self._makeOne().listInterfaces()
        self.assertIn(IRolesPlugin.__name__, listed)


class IRoleAssignerPlugin_conformance:

    def test_RoleAssignerPlugin_conformance(self):

        from ..interfaces.plugins import IRoleAssignerPlugin

        verifyClass(IRoleAssignerPlugin, self._getTargetClass())

    def test_IRoleAssignerPlugin_listInterfaces(self):

        from ..interfaces.plugins import IRoleAssignerPlugin

        listed = self._makeOne().listInterfaces()
        self.assertIn(IRoleAssignerPlugin.__name__, listed)


class IChallengeProtocolChooser_conformance:

    def test_ChallengeProtocolChooser_conformance(self):

        from ..interfaces.plugins import IChallengeProtocolChooser

        verifyClass(IChallengeProtocolChooser, self._getTargetClass())

    def test_IChallengeProtocolChooser_listInterfaces(self):

        from ..interfaces.plugins import IChallengeProtocolChooser

        listed = self._makeOne().listInterfaces()
        self.assertIn(IChallengeProtocolChooser.__name__, listed)


class IRequestTypeSniffer_conformance:

    def test_RequestTypeSniffer_conformance(self):

        from ..interfaces.plugins import IRequestTypeSniffer

        verifyClass(IRequestTypeSniffer, self._getTargetClass())

    def test_IRequestTypeSniffer_listInterfaces(self):

        from ..interfaces.plugins import IRequestTypeSniffer

        listed = self._makeOne().listInterfaces()
        self.assertIn(IRequestTypeSniffer.__name__, listed)


class IUserFolder_conformance:

    def test_conformance_IUserFolder(self):

        from ..interfaces.authservice import IUserFolder

        verifyClass(IUserFolder, self._getTargetClass())


class IBasicUser_conformance:

    def test_conformance_IBasicUser(self):

        from ..interfaces.authservice import IBasicUser

        verifyClass(IBasicUser, self._getTargetClass())


class IPropertiedUser_conformance:

    def test_conformance_IPropertiedUser(self):

        from ..interfaces.authservice import IPropertiedUser

        verifyClass(IPropertiedUser, self._getTargetClass())


class IPropertySheet_conformance:

    def test_conformance_IPropertySheet(self):

        from ..interfaces.propertysheets import IPropertySheet

        verifyClass(IPropertySheet, self._getTargetClass())


class INotCompetentPlugin_conformance:

    def test_INotCompetentPlugin_conformance(self):

        from ..interfaces.plugins import INotCompetentPlugin

        verifyClass(INotCompetentPlugin, self._getTargetClass())

    def test_INotCompetentPlugin_listInterfaces(self):

        from ..interfaces.plugins import INotCompetentPlugin

        listed = self._makeOne().listInterfaces()
        self.assertIn(INotCompetentPlugin.__name__, listed)
