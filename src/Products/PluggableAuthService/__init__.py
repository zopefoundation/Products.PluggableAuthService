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
""" PluggableAuthService product initialization.
"""

try:
    import ZServer  # noqa
except ImportError:
    HAVE_ZSERVER = False
else:
    HAVE_ZSERVER = True

from AccessControl.Permissions import manage_users as ManageUsers
from App.Management import Navigation

from Products.GenericSetup import BASE
from Products.GenericSetup import profile_registry
from Products.GenericSetup.tool import SetupTool

from . import PluggableAuthService
from .interfaces.authservice import IPluggableAuthService
from .permissions import ManageGroups
from .PluggableAuthService import registerMultiPlugin
from .plugins import ChallengeProtocolChooser as CPC
from .plugins import CookieAuthHelper as CAH
from .plugins import DelegatingMultiPlugin as DMP
from .plugins import DomainAuthHelper as DAH
from .plugins import DynamicGroupsPlugin as DGP
from .plugins import HTTPBasicAuthHelper as HBAH
from .plugins import InlineAuthHelper as IAH
from .plugins import LocalRolePlugin
from .plugins import NotCompetentHelper as NCH
from .plugins import RecursiveGroupsPlugin as RGP
from .plugins import RequestTypeSniffer as RTS
from .plugins import ScriptablePlugin
from .plugins import SearchPrincipalsPlugin as SPP
from .plugins import SessionAuthHelper as SAH
from .plugins import ZODBGroupManager
from .plugins import ZODBRoleManager
from .plugins import ZODBUserManager


registerMultiPlugin(HBAH.HTTPBasicAuthHelper.meta_type)
registerMultiPlugin(IAH.InlineAuthHelper.meta_type)
registerMultiPlugin(DAH.DomainAuthHelper.meta_type)
registerMultiPlugin(SAH.SessionAuthHelper.meta_type)
registerMultiPlugin(CAH.CookieAuthHelper.meta_type)
registerMultiPlugin(ScriptablePlugin.ScriptablePlugin.meta_type)
registerMultiPlugin(ZODBGroupManager.ZODBGroupManager.meta_type)
registerMultiPlugin(ZODBUserManager.ZODBUserManager.meta_type)
registerMultiPlugin(ZODBRoleManager.ZODBRoleManager.meta_type)
registerMultiPlugin(LocalRolePlugin.LocalRolePlugin.meta_type)
registerMultiPlugin(DMP.DelegatingMultiPlugin.meta_type)
registerMultiPlugin(SPP.SearchPrincipalsPlugin.meta_type)
registerMultiPlugin(RGP.RecursiveGroupsPlugin.meta_type)
registerMultiPlugin(DGP.DynamicGroupsPlugin.meta_type)
registerMultiPlugin(CPC.ChallengeProtocolChooser.meta_type)
registerMultiPlugin(RTS.RequestTypeSniffer.meta_type)
registerMultiPlugin(NCH.NotCompetent_byRoles.meta_type)
registerMultiPlugin(SetupTool.meta_type)


# monkey patch Zope to cause zmi logout to be PAS-aware
zope_manage_zmi_logout = Navigation.manage_zmi_logout


def manage_zmi_logout(self, REQUEST, RESPONSE):
    """Logout current user"""
    # keep despite doubt that it will work
    p = getattr(REQUEST, '_logout_path', None)
    if p is not None:
        return self.restrictedTraverse(p)

    from AccessControl import getSecurityManager
    user = getSecurityManager().getUser()
    if user is None or 'Authenticated' not in user.getRoles():
        return 'You are not/no longer logged in'

    acl_users = user.aq_parent

    if IPluggableAuthService.providedBy(acl_users):
        return acl_users.logout(REQUEST)
    else:
        return zope_manage_zmi_logout(self, REQUEST, RESPONSE)


Navigation.manage_zmi_logout = manage_zmi_logout


def initialize(context):

    context.registerClass(PluggableAuthService.PluggableAuthService,
                          permission=ManageUsers,
                          constructors=(
                              PluggableAuthService.addPluggableAuthService,),
                          icon='www/PluggableAuthService.png')

    context.registerClass(HBAH.HTTPBasicAuthHelper,
                          permission=ManageUsers,
                          constructors=(HBAH.manage_addHTTPBasicAuthHelperForm,
                                        HBAH.addHTTPBasicAuthHelper),
                          visibility=None,
                          icon='plugins/www/HTTPBasicAuthHelper.png')

    context.registerClass(IAH.InlineAuthHelper, permission=ManageUsers,
                          constructors=(IAH.manage_addInlineAuthHelperForm,
                                        IAH.addInlineAuthHelper),
                          visibility=None,
                          icon='plugins/www/InlineAuthHelper.png')

    context.registerClass(CAH.CookieAuthHelper, permission=ManageUsers,
                          constructors=(CAH.manage_addCookieAuthHelperForm,
                                        CAH.addCookieAuthHelper),
                          visibility=None,
                          icon='plugins/www/CookieAuthHelper.gif')

    context.registerClass(DAH.DomainAuthHelper, permission=ManageUsers,
                          constructors=(DAH.manage_addDomainAuthHelperForm,
                                        DAH.manage_addDomainAuthHelper),
                          visibility=None,
                          icon='plugins/www/DomainAuthHelper.png')

    context.registerClass(SAH.SessionAuthHelper, permission=ManageUsers,
                          constructors=(SAH.manage_addSessionAuthHelperForm,
                                        SAH.manage_addSessionAuthHelper),
                          visibility=None,
                          icon='plugins/www/SessionAuthHelper.gif')

    context.registerClass(ScriptablePlugin.ScriptablePlugin,
                          permission=ManageUsers,
                          constructors=(
                              ScriptablePlugin.manage_addScriptablePluginForm,
                              ScriptablePlugin.addScriptablePlugin),
                          visibility=None,
                          icon='plugins/www/ScriptablePlugin.png')

    context.registerClass(ZODBGroupManager.ZODBGroupManager,
                          permission=ManageGroups,
                          constructors=(
                              ZODBGroupManager.manage_addZODBGroupManagerForm,
                              ZODBGroupManager.addZODBGroupManager),
                          visibility=None,
                          icon='plugins/www/ZODBGroupManager.gif')

    context.registerClass(ZODBUserManager.ZODBUserManager,
                          permission=ManageUsers,
                          constructors=(
                              ZODBUserManager.manage_addZODBUserManagerForm,
                              ZODBUserManager.addZODBUserManager),
                          visibility=None,
                          icon='plugins/www/ZODBUserManager.gif')

    context.registerClass(ZODBRoleManager.ZODBRoleManager,
                          permission=ManageUsers,
                          constructors=(
                              ZODBRoleManager.manage_addZODBRoleManagerForm,
                              ZODBRoleManager.addZODBRoleManager),
                          visibility=None,
                          icon='plugins/www/ZODBRoleManager.gif')

    context.registerClass(LocalRolePlugin.LocalRolePlugin,
                          permission=ManageUsers,
                          constructors=(
                              LocalRolePlugin.manage_addLocalRolePluginForm,
                              LocalRolePlugin.addLocalRolePlugin),
                          visibility=None,
                          icon='plugins/www/ZODBRoleManager.gif')

    context.registerClass(DMP.DelegatingMultiPlugin, permission=ManageUsers,
                          constructors=(
                              DMP.manage_addDelegatingMultiPluginForm,
                              DMP.manage_addDelegatingMultiPlugin),
                          visibility=None,
                          icon='plugins/www/DelegatingMultiPlugin.png')

    context.registerClass(SPP.SearchPrincipalsPlugin, permission=ManageUsers,
                          constructors=(SPP.addSearchPrincipalsPluginForm,
                                        SPP.addSearchPrincipalsPlugin),
                          visibility=None,
                          icon='plugins/www/DelegatingMultiPlugin.png')

    context.registerClass(RGP.RecursiveGroupsPlugin, permission=ManageUsers,
                          constructors=(
                              RGP.manage_addRecursiveGroupsPluginForm,
                              RGP.addRecursiveGroupsPlugin),
                          visibility=None,
                          icon='plugins/www/RecursiveGroupsPlugin.png')

    context.registerClass(DGP.DynamicGroupsPlugin, permission=ManageUsers,
                          constructors=(DGP.manage_addDynamicGroupsPluginForm,
                                        DGP.addDynamicGroupsPlugin),
                          visibility=None,
                          icon='plugins/www/DynamicGroupsPlugin.png')

    context.registerClass(CPC.ChallengeProtocolChooser, permission=ManageUsers,
                          constructors=(
                              CPC.manage_addChallengeProtocolChooserForm,
                              CPC.addChallengeProtocolChooserPlugin),
                          visibility=None,
                          icon='plugins/www/DelegatingMultiPlugin.png')

    context.registerClass(RTS.RequestTypeSniffer, permission=ManageUsers,
                          constructors=(RTS.manage_addRequestTypeSnifferForm,
                                        RTS.addRequestTypeSnifferPlugin),
                          visibility=None,
                          icon='plugins/www/DelegatingMultiPlugin.png')

    context.registerClass(NCH.NotCompetent_byRoles, permission=ManageUsers,
                          constructors=(NCH.manage_addNotCompetent_byRolesForm,
                                        NCH.manage_addNotCompetent_byRoles),
                          visibility=None)

    context.registerClass(PluggableAuthService.PluggableAuthService,
                          meta_type='Configured PAS', permission=ManageUsers,
                          constructors=(
                              PluggableAuthService.addConfiguredPASForm,
                              PluggableAuthService.addConfiguredPAS),
                          icon='www/PluggableAuthService.png')

    try:
        profile_registry.getProfileInfo('PluggableAuthService:simple')
    except KeyError:
        # not yet registered
        profile_registry.registerProfile('simple',
                                         'Simple PAS Content Profile',
                                         'Content for a simple PAS.',
                                         'profiles/simple',
                                         'PluggableAuthService',
                                         BASE, IPluggableAuthService)

    try:
        profile_registry.getProfileInfo('PluggableAuthService:empty')
    except KeyError:
        # not yet registered
        profile_registry.registerProfile('empty', 'Empty PAS Content Profile',
                                         'Content for an empty PAS '
                                         '(plugins registry only).',
                                         'profiles/empty',
                                         'PluggableAuthService',
                                         BASE, IPluggableAuthService)
