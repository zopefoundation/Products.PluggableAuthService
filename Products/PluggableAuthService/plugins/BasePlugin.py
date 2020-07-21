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
""" Class: BasePlugin
"""

from AccessControl import ClassSecurityInfo
from AccessControl.class_init import InitializeClass
from Acquisition import aq_base
from Acquisition import aq_inner
from Acquisition import aq_parent
from OFS.PropertyManager import PropertyManager
from OFS.SimpleItem import SimpleItem
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from zope.interface import implementedBy
from zope.interface import providedBy

from Products.PluggableAuthService.permissions import ManageUsers
from Products.PluggableAuthService.utils import classImplements
from Products.PluggableAuthService.utils import createViewName


def flattenInterfaces(implemented):
    return implemented.flattened()


class BasePlugin(SimpleItem, PropertyManager):

    """ Base class for all PluggableAuthService Plugins
    """
    zmi_icon = 'fas fa-puzzle-piece'

    security = ClassSecurityInfo()

    manage_options = (({'label': 'Activate',
                        'action': 'manage_activateInterfacesForm'},)
                      + SimpleItem.manage_options
                      + PropertyManager.manage_options)

    prefix = ''

    _properties = (dict(id='prefix', type='string', mode='w',
                        label='Optional Prefix'),)

    security.declareProtected(ManageUsers,  # NOQA: D001
                              'manage_activateInterfacesForm')
    manage_activateInterfacesForm = PageTemplateFile(
        'www/bpActivateInterfaces', globals(),
        __name__='manage_activateInterfacesForm')

    @security.protected(ManageUsers)
    def listInterfaces(self):
        """ For ZMI update of interfaces. """

        results = []

        for iface in flattenInterfaces(providedBy(self)):
            results.append(iface.__name__)

        return results

    @security.protected(ManageUsers)
    def testImplements(self, interface):
        """ Can't access Interface.providedBy() directly in ZPT. """
        return interface.providedBy(self)

    @security.protected(ManageUsers)
    def manage_activateInterfaces(self, interfaces, RESPONSE=None):
        """ For ZMI update of active interfaces. """

        pas_instance = self._getPAS()
        plugins = pas_instance._getOb('plugins')

        active_interfaces = []

        for iface_name in interfaces:
            active_interfaces.append(plugins._getInterfaceFromName(
                                                iface_name))

        pt = plugins._plugin_types
        id = self.getId()

        for type in pt:
            ids = plugins.listPluginIds(type)
            if id not in ids and type in active_interfaces:
                plugins.activatePlugin(type, id)  # turn us on
            elif id in ids and type not in active_interfaces:
                plugins.deactivatePlugin(type, id)  # turn us off

        if RESPONSE is not None:
            RESPONSE.redirect('%s/manage_workspace'
                              '?manage_tabs_message='
                              'Interface+activations+updated.' %
                              self.absolute_url())

    @security.private
    def _getPAS(self):
        """ Canonical way to get at the PAS instance from a plugin """
        return aq_parent(aq_inner(self))

    @security.private
    def _invalidatePrincipalCache(self, id):
        pas = self._getPAS()
        if pas is not None and hasattr(aq_base(pas), 'ZCacheable_invalidate'):
            view_name = createViewName('_findUser', id)
            pas.ZCacheable_invalidate(view_name)

    @security.public
    def applyTransform(self, value):
        """ Transform for login name.

        Possibly transform the login, for example by making it lower
        case.

        Normally this is done in PAS itself, but in some cases a
        method in a plugin may need to do it itself, when there is no
        method in PAS that calls that method.
        """
        pas = self._getPAS()
        if pas is not None:
            return pas.applyTransform(value)
        return value


classImplements(BasePlugin, *implementedBy(SimpleItem))

InitializeClass(BasePlugin)
