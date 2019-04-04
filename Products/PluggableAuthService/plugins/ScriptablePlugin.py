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
""" Class: ScriptablePlugin
"""

import Products
from AccessControl import ClassSecurityInfo
from AccessControl.class_init import InitializeClass
from AccessControl.Permissions import manage_users as ManageUsers
from OFS.Folder import Folder
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from zope.interface import Interface
from zope.interface import implementedBy
from zope.interface import providedBy

from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin
from Products.PluggableAuthService.utils import classImplements
from Products.PluggableAuthService.utils import directlyProvides


class IScriptablePlugin(Interface):
    """ Marker interface.
    """


manage_addScriptablePluginForm = PageTemplateFile(
    'www/spAdd', globals(), __name__='manage_addScriptablePluginForm')


def addScriptablePlugin(dispatcher, id, title=None, REQUEST=None):
    """ Add a Scriptable Plugin to a Pluggable Auth Service. """

    sp = ScriptablePlugin(id, title)
    dispatcher._setObject(sp.getId(), sp)

    if REQUEST is not None:
        REQUEST['RESPONSE'].redirect('%s/manage_workspace'
                                     '?manage_tabs_message='
                                     'ScriptablePlugin+added.' %
                                     dispatcher.absolute_url())


class ScriptablePlugin(Folder, BasePlugin):

    """ Allow users to implement plugin interfaces using script objects.

    o Allowable types include ExternalMethods, Python Scripts, ZSQL Methods,
      and DTML methods.

    o Provide UI for creating scripts for known plugin types.
    """

    security = ClassSecurityInfo()

    meta_type = 'Scriptable Plugin'
    zmi_icon = 'fas fa-cogs'

    manage_options = ((Folder.manage_options[0],)
                      + ({'label': 'Interfaces',
                          'action': 'manage_editInterfacesForm'},)
                      + BasePlugin.manage_options)

    security.declareProtected(ManageUsers,  # NOQA: D001
                              'manage_editInterfacesForm')
    manage_editInterfacesForm = PageTemplateFile(
        'www/spEditInterfaces', globals(),
        __name__='manage_editInterfacesForm')

    def __creatable_by_emergency_user__(self):
        return 1

    def __init__(self, id, title=None):
        self._id = self.id = id
        self.title = title

    @security.protected(ManageUsers)
    def hasMethod(self, method_name):
        """ Do we implement this method directly?
        """
        return method_name in self.objectIds()

    @security.public
    def all_meta_types(self):
        """ What objects can be contained here? """
        allowed_types = ('Script (Python)', 'External Method', 'Z SQL Method',
                         'DTML Method', 'Page Template')

        return [x for x in Products.meta_types if x['name'] in allowed_types]

    @security.protected(ManageUsers)
    def _delOb(self, id):
        """
            Override ObjectManager's _delOb to account for removing any
            interface assertions the object might implement.
        """
        myId = self.getId()
        pas_instance = self._getPAS()
        plugins = pas_instance._getOb('plugins')
        curr_interfaces = set(providedBy(self))

        del_interfaces = set([x for x in providedBy(self) if id in x.names()])

        for interface in del_interfaces:
            if myId in plugins.listPluginIds(interface):
                plugins.deactivatePlugin(interface, myId)

        delattr(self, id)

        directlyProvides(self, *(list(curr_interfaces - del_interfaces)))

    @security.protected(ManageUsers)
    def manage_updateInterfaces(self, interfaces, RESPONSE=None):
        """ For ZMI update of interfaces. """

        pas_instance = self._getPAS()
        plugins = pas_instance._getOb('plugins')

        new_interfaces = []

        for interface in interfaces:
            new_interfaces.append(plugins._getInterfaceFromName(interface))

        klass_interfaces = [x for x in implementedBy(ScriptablePlugin)]
        directlyProvides(self, *(klass_interfaces + new_interfaces))

        if RESPONSE is not None:
            RESPONSE.redirect('%s/manage_workspace'
                              '?manage_tabs_message='
                              'Interfaces+updated.' % self.absolute_url())


classImplements(ScriptablePlugin, IScriptablePlugin,
                *(implementedBy(Folder) + implementedBy(BasePlugin)))

InitializeClass(ScriptablePlugin)
