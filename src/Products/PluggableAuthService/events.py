##############################################################################
#
# Copyright (c) 2007 Zope Foundation and Contributors
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
from Acquisition import aq_parent
from zope.component import adapter
from zope.component import subscribers
from zope.interface import implementer

from .interfaces.authservice import IBasicUser
from .interfaces.events import ICredentialsUpdatedEvent
from .interfaces.events import IGroupCreatedEvent
from .interfaces.events import IGroupDeletedEvent
from .interfaces.events import IPASEvent
from .interfaces.events import IPrincipalAddedToGroupEvent
from .interfaces.events import IPrincipalCreatedEvent
from .interfaces.events import IPrincipalDeletedEvent
from .interfaces.events import IPrincipalRemovedFromGroupEvent
from .interfaces.events import IPropertiesUpdatedEvent


@implementer(IPASEvent)
class PASEvent(object):

    def __init__(self, principal):
        self.principal = principal
        self.object = principal


@implementer(IPrincipalAddedToGroupEvent)
class PrincipalAddedToGroup(PASEvent):

    def __init__(self, principal, group_id):
        super(PrincipalAddedToGroup, self).__init__(principal)
        self.group_id = group_id


@implementer(IPrincipalRemovedFromGroupEvent)
class PrincipalRemovedFromGroup(PASEvent):

    def __init__(self, principal, group_id):
        super(PrincipalRemovedFromGroup, self).__init__(principal)
        self.group_id = group_id


@implementer(IPrincipalCreatedEvent)
class PrincipalCreated(PASEvent):
    pass


@implementer(IPrincipalDeletedEvent)
class PrincipalDeleted(PASEvent):
    pass


@implementer(IGroupCreatedEvent)
class GroupCreated(PASEvent):

    def __init__(self, group, plugin):
        super(GroupCreated, self).__init__(group)
        self.plugin = plugin


@implementer(IGroupDeletedEvent)
class GroupDeleted(PASEvent):
    pass


@implementer(ICredentialsUpdatedEvent)
class CredentialsUpdated(PASEvent):

    def __init__(self, principal, password):
        super(CredentialsUpdated, self).__init__(principal)
        self.password = password


@implementer(IPropertiesUpdatedEvent)
class PropertiesUpdated(PASEvent):

    def __init__(self, principal, properties):
        super(PropertiesUpdated, self).__init__(principal)
        self.properties = properties


@adapter(IBasicUser, ICredentialsUpdatedEvent)
def userCredentialsUpdatedHandler(principal, event):
    pas = aq_parent(principal)
    pas.updateCredentials(
        pas.REQUEST,
        pas.REQUEST.RESPONSE,
        principal.getUserName(),  # aka "login"
        event.password)


@adapter(IPASEvent)
def PASEventNotify(event):
    """Event subscriber to dispatch PASEvent to interested adapters."""
    adapters = subscribers((event.principal, event), None)
    for adapter_ in adapters:
        pass  # getting them does the work
