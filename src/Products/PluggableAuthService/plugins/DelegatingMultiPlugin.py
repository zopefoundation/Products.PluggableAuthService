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
""" DelegatingMultiPlugin   Shim to use any User Folder with the
                            PluggableAuthenticationService
"""

import copy

from AccessControl import AuthEncoding
from AccessControl import ClassSecurityInfo
from AccessControl.class_init import InitializeClass
from AccessControl.SpecialUsers import emergency_user
from Acquisition import aq_base
from OFS.Folder import Folder
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from zope.interface import Interface

from ..interfaces.plugins import IAuthenticationPlugin
from ..interfaces.plugins import ICredentialsResetPlugin
from ..interfaces.plugins import ICredentialsUpdatePlugin
from ..interfaces.plugins import IPropertiesPlugin
from ..interfaces.plugins import IRolesPlugin
from ..plugins.BasePlugin import BasePlugin
from ..utils import classImplements


class IDelegatingMultiPlugin(Interface):
    """ Marker interface.
    """


manage_addDelegatingMultiPluginForm = PageTemplateFile(
    'www/dmpAdd', globals(), __name__='manage_addDelegatingMultiPluginForm')


def manage_addDelegatingMultiPlugin(self, id, title='', delegate_path='',
                                    REQUEST=None):
    """ Factory method to instantiate a DelegatingMultiPlugin """
    # Make sure we really are working in our container (the
    # PluggableAuthService object)
    self = self.this()

    # Instantiate the folderish adapter object
    lmp = DelegatingMultiPlugin(id, title=title, delegate_path=delegate_path)
    self._setObject(id, lmp)

    if REQUEST is not None:
        REQUEST.RESPONSE.redirect('%s/manage_main' % self.absolute_url())


class DelegatingMultiPlugin(Folder, BasePlugin):
    """ The adapter that mediates between the PAS and the DelegatingUserFolder
    """
    security = ClassSecurityInfo()
    meta_type = 'Delegating Multi Plugin'
    zmi_icon = 'fas fa-external-link-alt'

    manage_options = BasePlugin.manage_options[:1] + Folder.manage_options

    _properties = ({'id': 'delegate', 'label': 'Delegate Path',
                    'type': 'string', 'mode': 'w'},)

    def __init__(self, id, title='', delegate_path=''):
        """ Initialize a new instance """
        self.id = id
        self.title = title
        self.delegate = delegate_path

    @security.private
    def _getUserFolder(self):
        """ Safely retrieve a User Folder to work with """
        uf = getattr(aq_base(self), 'acl_users', None)

        if uf is None and self.delegate:
            uf = self.unrestrictedTraverse(self.delegate)

        return uf

    @security.private
    def authenticateCredentials(self, credentials):
        """ Fulfill AuthenticationPlugin requirements """
        acl = self._getUserFolder()
        login = credentials.get('login', '')
        password = credentials.get('password', '')

        if not acl or not login or not password:
            return (None, None)

        if login == emergency_user.getUserName() and \
                AuthEncoding.pw_validate(emergency_user._getPassword(),
                                         password):
            return (login, login)

        user = acl.getUser(login)

        if user is None:
            return (None, None)

        elif user and AuthEncoding.pw_validate(user._getPassword(), password):
            return (user.getId(), login)

        return (None, None)

    @security.private
    def updateCredentials(self, request, response, login, new_password):
        """ Fulfill CredentialsUpdatePlugin requirements """
        # Need to at least remove user from cache
        pass

    @security.private
    def resetCredentials(self, request, response):
        """ Fulfill CredentialsResetPlugin requirements """
        # Remove user from cache?
        pass

    @security.private
    def getPropertiesForUser(self, user, request=None):
        """ Fullfill PropertiesPlugin requirements """
        acl = self._getUserFolder()

        if acl is None:
            return {}

        user = acl.getUserById(user.getId())

        if user is None:
            return {}

        # WAAA
        return copy.deepcopy(user.__dict__)

    @security.private
    def getRolesForPrincipal(self, user, request=None):
        """ Fullfill RolesPlugin requirements """
        acl = self._getUserFolder()

        if acl is None:
            return ()

        user = acl.getUserById(user.getId())

        if user is None:
            return ()

        return tuple(user.getRoles())

    @security.private
    def enumerateUsers(self, id=None, login=None, exact_match=0, sort_by=None,
                       max_results=None, **kw):
        """ Fulfill the EnumerationPlugin requirements """
        result = []
        acl = self._getUserFolder()
        plugin_id = self.getId()
        edit_url = f'{plugin_id}/{acl.getId()}/manage_userrecords'

        if acl is None:
            return ()

        if exact_match:
            if id:
                user = acl.getUserById(id)
            elif login:
                user = acl.getUser(login)
            else:
                msg = 'Exact Match specified but no ID or Login given'
                raise ValueError(msg)

            if user is not None:
                result.append({'id': user.getId(), 'login': user.getUserName(),
                               'pluginid': plugin_id,
                               'editurl': '%s' % edit_url})
        else:
            # WAAAAA!!!!
            all_users = acl.getUsers()

            for user in all_users:
                if id:
                    if user.getId().find(id) != -1:
                        result.append({'login': user.getUserName(),
                                       'id': user.getId(),
                                       'pluginid': plugin_id})
                elif login:
                    if user.getUserName().find(login) != -1:
                        result.append({'login': user.getUserName(),
                                       'id': user.getId(),
                                       'pluginid': plugin_id})

            if sort_by is not None:
                result = sorted(key=lambda x: x.get(sort_by, '').lower())

            if max_results is not None:
                try:
                    max_results = int(max_results)
                    result = result[:max_results + 1]
                except ValueError:
                    pass

        return tuple(result)


classImplements(DelegatingMultiPlugin, IDelegatingMultiPlugin,
                IAuthenticationPlugin, IRolesPlugin,
                ICredentialsUpdatePlugin, ICredentialsResetPlugin,
                IPropertiesPlugin)


InitializeClass(DelegatingMultiPlugin)
