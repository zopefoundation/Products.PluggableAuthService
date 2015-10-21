# -*- coding: utf-8 -*-
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
from Products.PluggableAuthService.interfaces import events
from Products.PluggableAuthService.interfaces.authservice import IBasicUser
from zope.component import adapter
from zope.component import subscribers
from zope.interface import implementer


@implementer(events.IPASEvent)
class PASEvent(object):

    def __init__(self, principal):
        self.principal = principal
        self.object = principal


@implementer(events.IPrincipalCreatedEvent)
class PrincipalCreated(PASEvent):
    pass


@implementer(events.IPrincipalDeletedEvent)
class PrincipalDeleted(PASEvent):
    pass


@implementer(events.ICredentialsUpdatedEvent)
class CredentialsUpdated(PASEvent):

    def __init__(self, principal, password):
        super(CredentialsUpdated, self).__init__(principal)
        self.password = password


@implementer(events.IPropertiesUpdatedEvent)
class PropertiesUpdated(PASEvent):

    def __init__(self, principal, properties):
        super(PropertiesUpdated, self).__init__(principal)
        self.properties = properties


@adapter(IBasicUser, events.ICredentialsUpdatedEvent)
def userCredentialsUpdatedHandler(principal, event):
    pas = aq_parent(principal)
    pas.updateCredentials(
        pas,
        pas.REQUEST,
        pas.REQUEST.RESPONSE,
        principal.getId(),
        event.password)


@adapter(events.IPASEvent)
def PASEventNotify(event):
    """Event subscriber to dispatch PASEvent to interested adapters."""
    adapters = subscribers((event.principal, event), None)
    for ad in adapters:
        pass  # getting them does the work
