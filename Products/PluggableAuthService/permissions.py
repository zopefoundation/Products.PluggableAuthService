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
""" Product-specifict permissions.
"""
from AccessControl import ModuleSecurityInfo
from AccessControl import Permissions
from AccessControl.Permission import addPermission


security = ModuleSecurityInfo('Products.PluggableAuthService.permissions')

security.declarePublic('ManageUsers')  # NOQA: D001
ManageUsers = Permissions.manage_users

security.declarePublic('ManageGroups')  # NOQA: D001
ManageGroups = 'Manage Groups'


@security.private
def setDefaultRoles(permission, roles):
    """ Set the defaults roles for a permission.
    """
    addPermission(permission, roles)


security.declarePublic('SearchPrincipals')  # NOQA: D001
SearchPrincipals = 'Search for principals'
setDefaultRoles(SearchPrincipals, ('Manager',))

security.declarePublic('SetOwnPassword')  # NOQA: D001
SetOwnPassword = 'Set own password'
setDefaultRoles(SetOwnPassword, ('Authenticated',))
