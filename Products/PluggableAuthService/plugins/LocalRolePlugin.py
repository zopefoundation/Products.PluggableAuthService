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
""" Classes: LocalRolePlugin
"""

from AccessControl import ClassSecurityInfo
from AccessControl.class_init import InitializeClass
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from zope.interface import Interface

from Products.PluggableAuthService.interfaces.plugins import IRolesPlugin
from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin
from Products.PluggableAuthService.utils import classImplements


class ILocalRolePlugin(Interface):
    """ Marker interface.
    """


manage_addLocalRolePluginForm = PageTemplateFile(
    'www/lrpAdd', globals(), __name__='manage_addLocalRolePluginForm')


def addLocalRolePlugin(dispatcher, id, title='', RESPONSE=None):
    """ Add a Local Role Plugin to 'dispatcher'.
    """

    lrp = LocalRolePlugin(id, title)
    dispatcher._setObject(id, lrp)

    if RESPONSE is not None:
        msg = '%s/manage_main?manage_tabs_message=%s'
        goto = dispatcher.absolute_url()
        RESPONSE.redirect(msg % (goto, 'LocalRolePlugin+added.'))


class LocalRolePlugin(BasePlugin):
    """ Provide roles during Authentication from local roles
        assignments made on the root object.
    """

    meta_type = 'Local Role Plugin'
    zmi_icon = 'fas fa-user-tag'
    security = ClassSecurityInfo()

    def __init__(self, id, title=None):
        self._setId(id)
        self.title = title

    #
    #    IRolesPlugin implementation
    #
    @security.private
    def getRolesForPrincipal(self, principal, request=None):

        """ See IRolesPlugin.
        """
        local_roles = getattr(self.getPhysicalRoot(),
                              '__ac_local_roles__', None)
        if local_roles is None:
            return None
        return local_roles.get(principal.getId())


classImplements(LocalRolePlugin, ILocalRolePlugin, IRolesPlugin)

InitializeClass(LocalRolePlugin)
