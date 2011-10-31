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
from zope.interface import implements

from Products.PluggableAuthService.interfaces.authservice import IBasicUser
from Products.PluggableAuthService.interfaces.events \
    import ICredentialsUpdatedEvent
from Products.PluggableAuthService.interfaces.events import IPASEvent
from Products.PluggableAuthService.interfaces.events \
    import IPrincipalCreatedEvent
from Products.PluggableAuthService.interfaces.events \
    import IPrincipalDeletedEvent
from Products.PluggableAuthService.interfaces.events \
    import IPropertiesUpdatedEvent


class PASEvent(object):
    implements(IPASEvent)

    def __init__(self, principal):
        self.principal = principal
        self.object = principal


class PrincipalCreated(PASEvent):
    implements(IPrincipalCreatedEvent)


class PrincipalDeleted(PASEvent):
    implements(IPrincipalDeletedEvent)


class CredentialsUpdated(PASEvent):
    implements(ICredentialsUpdatedEvent)

    def __init__(self, principal, password):
        super(CredentialsUpdated, self).__init__(principal)
        self.password = password


class PropertiesUpdated(PASEvent):
    implements(IPropertiesUpdatedEvent)

    def __init__(self, principal, properties):
        super(PropertiesUpdated, self).__init__(principal)
        self.properties = properties


@adapter(IBasicUser, ICredentialsUpdatedEvent)
def userCredentialsUpdatedHandler(principal, event):
    pas = aq_parent(principal)
    pas.updateCredentials(
            pas,
            pas.REQUEST,
            pas.REQUEST.RESPONSE,
            principal.getId(),
            event.password)


@adapter(IPASEvent)
def PASEventNotify(event):
    """Event subscriber to dispatch PASEvent to interested adapters."""
    adapters = subscribers((event.principal, event), None)
    for adapter in adapters:
        pass # getting them does the work

