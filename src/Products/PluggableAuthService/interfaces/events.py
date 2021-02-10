from zope.interface import Attribute
from zope.interface import Interface


class IPASEvent(Interface):
    """An event related to a PAS principal.
    """

    principal = Attribute('The subject of the event.')


class IPrincipalAddedToGroupEvent(IPASEvent):
    """A principal has been added to a group.
    """
    group_id = Attribute('Group ID to which principal is being added')


class IPrincipalRemovedFromGroupEvent(IPASEvent):
    """A principal has been removed from a group.
    """
    group_id = Attribute('Group ID from which principal is being removed')


class IPrincipalCreatedEvent(IPASEvent):
    """A new principal has been created.
    """


class IUserLoggedInEvent(IPASEvent):
    """ A user logged in.
    """


class IUserLoggedOutEvent(IPASEvent):
    """ A user logged out.
    """


class IPrincipalDeletedEvent(IPASEvent):
    """A user has been removed.
    """


class ICredentialsUpdatedEvent(IPASEvent):
    """A principal has changed her password.

    Sending this event will cause a PAS user folder to trigger its active
    credential update plugins.
    """
    password = Attribute('The new password')


class IPropertiesUpdatedEvent(IPASEvent):
    """A principals properties have been updated.
    """
    properties = Attribute('List of modified property ids')


class IGroupCreatedEvent(IPASEvent):
    """A group has been created.
    """


class IGroupDeletedEvent(IPASEvent):
    """A group has been removed.
    """
