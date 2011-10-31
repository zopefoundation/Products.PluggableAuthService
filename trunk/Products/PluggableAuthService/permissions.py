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

$Id$
"""
from AccessControl import ModuleSecurityInfo
from AccessControl import Permissions

security = ModuleSecurityInfo( 'Products.PluggableAuthService.permissions' )

security.declarePublic( 'ManageUsers' )
ManageUsers = Permissions.manage_users

security.declarePublic( 'ManageGroups' )
ManageGroups = "Manage Groups"

addPermission = None
try:
    from AccessControl.Permission import addPermission
except ImportError:
    pass

security.declarePrivate( 'setDefaultRoles' )
def setDefaultRoles( permission, roles ):
    """ Set the defaults roles for a permission.
    """
    if addPermission is not None:
        addPermission(permission, roles)
    else:
        # BBB This is in AccessControl starting in Zope 2.13
        from AccessControl.Permission import _registeredPermissions
        from AccessControl.Permission import pname
        from AccessControl.Permission import ApplicationDefaultPermissions
        import Products
        registered = _registeredPermissions
        if not registered.has_key( permission ):
            registered[ permission ] = 1
            Products.__ac_permissions__=(
                Products.__ac_permissions__+((permission,(),roles),))
            mangled = pname(permission)
            setattr(ApplicationDefaultPermissions, mangled, roles)


security.declarePublic( 'SearchPrincipals' )
SearchPrincipals = 'Search for principals'
setDefaultRoles( SearchPrincipals, ( 'Manager', ) )

security.declarePublic( 'SetOwnPassword' )
SetOwnPassword = 'Set own password'
setDefaultRoles( SetOwnPassword, ( 'Authenticated', ) )
