##############################################################################
#
# Copyright (c) 2012 Zope Foundation and Contributors
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
""" NotCompetentHelper   `INotCompetent` plugin utilities

`INotCompetent` plugins are usually used to prevent shadowing of users
authenticated by higher level user folders. This module provides
an `INotCompetent` plugin base class which can check for authentications
by higher level user folders and the class `NotCompetent_byRoles`
to prevent shadowing of higher level authentications with
specified roles.
"""

from AccessControl import ClassSecurityInfo
from AccessControl.Permissions import manage_users
from AccessControl.User import nobody
from Acquisition import aq_base
from Acquisition import aq_inner
from Acquisition import aq_parent
from OFS.PropertyManager import PropertyManager
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from ZPublisher.BaseRequest import UNSPECIFIED_ROLES
from ZPublisher.HTTPResponse import HTTPResponse as Response

from Products.PluggableAuthService.interfaces.plugins import \
    INotCompetentPlugin
from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin
from Products.PluggableAuthService.utils import classImplements


class HigherLevelUserFolderAccessMixin(object):
    """mixin class for access to higher level user folders

       requires to be mixed with a `BasePlugin`.
    """
    def _generateHigherLevelUserFolders(self):
        folder = aq_parent(aq_inner(self._getPAS()))
        while True:
            folder = aq_parent(aq_inner(folder))
            if folder is None:
                return
            uf = getattr(folder, '__allow_groups__', None)
            validate = getattr(aq_base(uf), 'validate', None)
            if validate is not None:
                yield uf

    def _getHigherLevelUser(self, request, roles=None):
        if roles:
            accessed = self._getPAS()._getObjectContext(
                request['PUBLISHED'], request)[1]
        req_roles = request.roles
        auth = request._auth
        # save response and install new one to prevent side effects
        saved_response = request.response
        try:
            request.response = Response()
            for uf in self._generateHigherLevelUserFolders():
                if req_roles is UNSPECIFIED_ROLES:
                    u = uf.validate(request, auth)
                else:
                    u = uf.validate(request, auth, req_roles)
                if u is None or u is nobody:
                    continue
                # this user folder has authenticated a user able to perform
                # the request
                if roles:
                    # check in addition that is has one of *roles*
                    if not u.allowed(accessed, roles):
                        # reject this user
                        continue
                return u
        finally:
            request.response = saved_response


class NotCompetentBase(BasePlugin, HigherLevelUserFolderAccessMixin):
    """abstract `INotCompententPlugin` base class.

    with access to higher level user folders.
    """

    security = ClassSecurityInfo()
    security.declareObjectProtected(manage_users)

    def __init__(self, id, title=''):
        self.id = id
        self.title = title

    @security.private
    def isNotCompetentToAuthenticate(self, request):
        raise NotImplementedError()


classImplements(NotCompetentBase, INotCompetentPlugin)


class NotCompetent_byRoles(NotCompetentBase):
    """`INotCompetentPlugin` to prevent authentication shadowing by roles.
    """

    meta_type = 'prevent authentication shaddowing by roles'

    _properties = (
        PropertyManager._properties +
        (dict(id='roles', label='roles (empty means all roles)',
              type='lines', mode='rw'),))
    roles = ()

    manage_options = (
        (NotCompetentBase.manage_options[0],)
        + PropertyManager.manage_options
        + NotCompetentBase.manage_options[1:-1])

    def isNotCompetentToAuthenticate(self, request):
        return self._getHigherLevelUser(request, self.roles) is not None


manage_addNotCompetent_byRolesForm = PageTemplateFile(
    'www/ncbrAdd', globals(), __name__='manage_addNotCompetent_byRolesForm')


def manage_addNotCompetent_byRoles(self, id, title='', REQUEST=None):
    """ Factory method to instantiate a NotCompetent_byRoles """
    obj = NotCompetent_byRoles(id, title=title)
    self._setObject(id, obj)

    if REQUEST is not None:
        qs = 'manage_tabs_message=NotCompetent_byRoles+added.'
        my_url = self.absolute_url()
        REQUEST['RESPONSE'].redirect('%s/manage_workspace?%s' % (my_url, qs))
