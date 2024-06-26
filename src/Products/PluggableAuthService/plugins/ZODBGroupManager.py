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
""" Classes: ZODBGroupManager
"""


from AccessControl import ClassSecurityInfo
from AccessControl.class_init import InitializeClass
from AccessControl.requestmethod import postonly
from Acquisition import aq_parent
from BTrees.OOBTree import OOBTree
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from zope.event import notify
from zope.interface import Interface

from ..events import GroupCreated
from ..events import PrincipalAddedToGroup
from ..events import PrincipalRemovedFromGroup
from ..interfaces.plugins import IGroupEnumerationPlugin
from ..interfaces.plugins import IGroupsPlugin
from ..permissions import ManageGroups
from ..plugins.BasePlugin import BasePlugin
from ..utils import classImplements
from ..utils import csrf_only


class IZODBGroupManager(Interface):
    """ Marker interface.
    """


manage_addZODBGroupManagerForm = PageTemplateFile(
    'www/zgAdd', globals(), __name__='manage_addZODBGroupManagerForm')


def addZODBGroupManager(dispatcher, id, title=None, REQUEST=None):
    """ Add a ZODBGroupManager to a Pluggable Auth Service. """

    zgm = ZODBGroupManager(id, title)
    dispatcher._setObject(zgm.getId(), zgm)

    if REQUEST is not None:
        REQUEST['RESPONSE'].redirect('%s/manage_workspace'
                                     '?manage_tabs_message='
                                     'ZODBGroupManager+added.' %
                                     dispatcher.absolute_url())


class ZODBGroupManager(BasePlugin):

    """ PAS plugin for managing groups, and groups of groups in the ZODB
    """
    meta_type = 'ZODB Group Manager'
    zmi_icon = 'fas fa-users'

    security = ClassSecurityInfo()

    def __init__(self, id, title=None):

        self._id = self.id = id
        self.title = title
        self._groups = OOBTree()
        self._principal_groups = OOBTree()

    #
    #   IGroupEnumerationPlugin implementation
    #
    @security.private
    def enumerateGroups(self, id=None, title=None, exact_match=False,
                        sort_by=None, max_results=None, **kw):
        """ See IGroupEnumerationPlugin.
        """
        group_info = []
        group_ids = []
        plugin_id = self.getId()

        if isinstance(id, str):
            id = [id]

        if isinstance(title, str):
            title = [title]

        if exact_match and (id or title):

            if id:
                group_ids.extend(id)
            elif title:
                group_ids.extend(title)

        if group_ids:
            group_filter = None

        else:   # Searching
            group_ids = self.listGroupIds()
            group_filter = _ZODBGroupFilter(id, title, **kw)

        for group_id in group_ids:

            if self._groups.get(group_id, None):
                e_url = '%s/manage_groups' % self.getId()
                p_qs = 'group_id=%s' % group_id
                m_qs = 'group_id=%s&assign=1' % group_id

                info = {}
                info.update(self._groups[group_id])

                info['pluginid'] = plugin_id
                info['properties_url'] = f'{e_url}?{p_qs}'
                info['members_url'] = f'{e_url}?{m_qs}'

                info['id'] = '{}{}'.format(self.prefix, info['id'])

                if not group_filter or group_filter(info):
                    group_info.append(info)

        return tuple(group_info)

    #
    #   IGroupsPlugin implementation
    #
    @security.private
    def getGroupsForPrincipal(self, principal, request=None):
        """ See IGroupsPlugin.
        """
        unadorned = self._principal_groups.get(principal.getId(), ())
        return tuple([f'{self.prefix}{x}' for x in unadorned])

    #
    #   (notional)IZODBGroupManager interface
    #
    @security.protected(ManageGroups)
    def listGroupIds(self):
        """ -> (group_id_1, ... group_id_n)
        """
        return self._groups.keys()

    @security.protected(ManageGroups)
    def listGroupInfo(self):
        """ -> (dict, ...dict)

        o Return one mapping per group, with the following keys:

          - 'id'
        """
        return self._groups.values()

    @security.protected(ManageGroups)
    def getGroupInfo(self, group_id):
        """ group_id -> dict
        """
        return self._groups[group_id]

    @security.private
    def addGroup(self, group_id, title=None, description=None):
        """ Add 'group_id' to the list of groups managed by this object.

        o Raise KeyError on duplicate.
        """
        if self._groups.get(group_id) is not None:
            raise KeyError('Duplicate group ID: %s' % group_id)

        self._groups[group_id] = {'id': group_id, 'title': title,
                                  'description': description}
        notify(GroupCreated(group_id, self))

    @security.private
    def updateGroup(self, group_id, title=None, description=None):
        """ Update properties for 'group_id'

        o Raise KeyError if group_id doesn't already exist.
        """
        if title is not None:
            self._groups[group_id]['title'] = title
        if description is not None:
            self._groups[group_id]['description'] = description
        self._groups[group_id] = self._groups[group_id]

    @security.private
    def removeGroup(self, group_id):
        """ Remove 'role_id' from the list of roles managed by this
            object, removing assigned members from it before doing so.

        o Raise KeyError if 'group_id' doesn't already exist.
        """
        for principal_id in self._principal_groups.keys():
            self.removePrincipalFromGroup(principal_id, group_id)
        del self._groups[group_id]

    #
    #   Group assignment API
    #
    @security.protected(ManageGroups)
    def listAvailablePrincipals(self, group_id, search_id):
        """ Return a list of principal IDs to that can belong to the group.

        o If supplied, 'search_id' constrains the principal IDs;  if not,
          return empty list.

        o Omit principals with existing assignments.
        """
        result = []

        if search_id:  # don't bother searching if no criteria

            parent = aq_parent(self)

            for info in parent.searchPrincipals(max_results=20, sort_by='id',
                                                id=search_id,
                                                exact_match=False):
                id = info['id']
                title = info.get('title', id)
                if group_id not in self._principal_groups.get(id, ()) \
                        and group_id != id:
                    result.append((id, title))

        return result

    @security.protected(ManageGroups)
    def listAssignedPrincipals(self, group_id):
        """ Return a list of principal IDs belonging to a group.
        """
        result = []

        for k, v in self._principal_groups.items():
            if group_id in v:
                parent = aq_parent(self)
                info = parent.searchPrincipals(id=k, exact_match=True)
                if len(info) == 0:
                    title = '<%s: not found>' % k
                else:
                    # always use the title of the first principal found
                    title = info[0].get('title', k)
                result.append((k, title))

        return result

    @security.private
    def addPrincipalToGroup(self, principal_id, group_id):
        """ Add a principal to a group.

        o Return a boolean indicating whether a new assignment was created.

        o Raise KeyError if 'group_id' is unknown.
        """
        # raise KeyError if unknown!
        group_info = self._groups[group_id]  # noqa

        current = self._principal_groups.get(principal_id, ())
        already = group_id in current

        if not already:
            new = current + (group_id,)
            self._principal_groups[principal_id] = new
            self._invalidatePrincipalCache(principal_id)
            notify(PrincipalAddedToGroup(principal_id, group_id))

        return not already

    @security.private
    def removePrincipalFromGroup(self, principal_id, group_id):
        """ Remove a prinicpal from from a group.

        o Return a boolean indicating whether the principal was already
          a member of the group.

        o Raise KeyError if 'group_id' is unknown.

        o Ignore requests to remove a principal if not already a member
          of the group.
        """
        # raise KeyError if unknown!
        group_info = self._groups[group_id]  # noqa

        current = self._principal_groups.get(principal_id, ())
        new = tuple([x for x in current if x != group_id])
        already = current != new

        if already:
            self._principal_groups[principal_id] = new
            self._invalidatePrincipalCache(principal_id)
            notify(PrincipalRemovedFromGroup(principal_id, group_id))

        return already

    #
    #   ZMI
    #
    manage_options = (({'label': 'Groups', 'action': 'manage_groups'},)
                      + BasePlugin.manage_options)

    security.declarePublic('manage_widgets')  # NOQA: D001
    manage_widgets = PageTemplateFile('www/zuWidgets', globals(),
                                      __name__='manage_widgets')

    security.declareProtected(ManageGroups, 'manage_groups')  # NOQA: D001
    manage_groups = PageTemplateFile('www/zgGroups', globals(),
                                     __name__='manage_groups')

    security.declareProtected(ManageGroups, 'manage_twoLists')  # NOQA: D001
    manage_twoLists = PageTemplateFile('../www/two_lists', globals(),
                                       __name__='manage_twoLists')

    @security.protected(ManageGroups)
    def manage_addGroup(self, group_id, title=None, description=None,
                        RESPONSE=None):
        """ Add a group via the ZMI.
        """
        if not group_id:
            message = 'Please+provide+a+Group+ID'
        else:
            self.addGroup(group_id, title, description)
            message = 'Group+added'

        if RESPONSE is not None:
            RESPONSE.redirect('%s/manage_groups?manage_tabs_message=%s' %
                              (self.absolute_url(), message))

    @security.protected(ManageGroups)
    def manage_updateGroup(self, group_id, title, description, RESPONSE=None):
        """ Update a group via the ZMI.
        """
        self.updateGroup(group_id, title, description)

        message = 'Group+updated'

        if RESPONSE is not None:
            RESPONSE.redirect('%s/manage_groups?manage_tabs_message=%s' %
                              (self.absolute_url(), message))

    @security.protected(ManageGroups)
    @csrf_only
    @postonly
    def manage_removeGroups(self, group_ids, RESPONSE=None, REQUEST=None):
        """ Remove one or more groups via the ZMI.
        """
        group_ids = [_f for _f in group_ids if _f]

        if not group_ids:
            message = 'no+groups+selected'

        else:

            for group_id in group_ids:
                self.removeGroup(group_id)

            message = 'Groups+removed'

        if RESPONSE is not None:
            RESPONSE.redirect('%s/manage_groups?manage_tabs_message=%s' %
                              (self.absolute_url(), message))

    @security.protected(ManageGroups)
    @csrf_only
    @postonly
    def manage_addPrincipalsToGroup(self, group_id, principal_ids,
                                    RESPONSE=None, REQUEST=None):
        """ Add one or more principals to a group via the ZMI.
        """
        assigned = []

        for principal_id in principal_ids:
            if self.addPrincipalToGroup(principal_id, group_id):
                assigned.append(principal_id)

        if not assigned:
            message = 'Principals+already+members+of+%s' % group_id
        else:
            message = '{}+added+to+{}'.format('+'.join(assigned), group_id)

        if RESPONSE is not None:
            RESPONSE.redirect('%s/manage_groups?group_id=%s&assign=1'
                              '&manage_tabs_message=%s' %
                              (self.absolute_url(), group_id, message))

    @security.protected(ManageGroups)
    @csrf_only
    @postonly
    def manage_removePrincipalsFromGroup(self, group_id, principal_ids,
                                         RESPONSE=None, REQUEST=None):
        """ Remove one or more principals from a group via the ZMI.
        """
        removed = []

        for principal_id in principal_ids:
            if self.removePrincipalFromGroup(principal_id, group_id):
                removed.append(principal_id)

        if not removed:
            message = 'Principals+not+in+group+%s' % group_id
        else:
            message = 'Principals+{}+removed+from+{}'.format(
                '+'.join(removed), group_id)

        if RESPONSE is not None:
            RESPONSE.redirect('%s/manage_groups?group_id=%s&assign=1'
                              '&manage_tabs_message=%s' %
                              (self.absolute_url(), group_id, message))


classImplements(ZODBGroupManager, IZODBGroupManager, IGroupEnumerationPlugin,
                IGroupsPlugin)


InitializeClass(ZODBGroupManager)


class _ZODBGroupFilter:

    def __init__(self, id=None, title=None, **kw):

        self._filter_ids = id
        self._filter_titles = title

    def __call__(self, group_info):

        if self._filter_ids:

            key = 'id'
            to_test = self._filter_ids

        elif self._filter_titles:

            key = 'title'
            to_test = self._filter_titles

        else:
            return 1  # ???:  try using 'kw'

        value = group_info.get(key)

        if not value:
            return 0

        for contained in to_test:
            if value.lower().find(contained.lower()) >= 0:
                return 1

        return 0
