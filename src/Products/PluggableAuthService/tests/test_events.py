##############################################################################
#
# Copyright (c) 2011 Zope Foundation and Contributors
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
import unittest


class ConformsToIPASEvent:

    def test_class_conforms_to_IPASEvent(self):
        from zope.interface.verify import verifyClass

        from ..interfaces.events import IPASEvent
        verifyClass(IPASEvent, self._getTargetClass())

    def test_instance_conforms_to_IPASEvent(self):
        from zope.interface.verify import verifyObject

        from ..interfaces.events import IPASEvent
        verifyObject(IPASEvent, self._makeOne())


class PASEventTests(unittest.TestCase, ConformsToIPASEvent):

    def _getTargetClass(self):
        from ..events import PASEvent
        return PASEvent

    def _makeOne(self, principal=None):
        if principal is None:
            principal = DummyPrincipal()
        return self._getTargetClass()(principal)


class PrincipalCreatedTests(unittest.TestCase, ConformsToIPASEvent):

    def _getTargetClass(self):
        from ..events import PrincipalCreated
        return PrincipalCreated

    def _makeOne(self, principal=None):
        if principal is None:
            principal = DummyPrincipal()
        return self._getTargetClass()(principal)

    def test_class_conforms_to_IPrincipalCreatedEvent(self):
        from zope.interface.verify import verifyClass

        from ..interfaces.events import IPrincipalCreatedEvent
        verifyClass(IPrincipalCreatedEvent, self._getTargetClass())

    def test_instance_conforms_to_IPrincipalCreatedEvent(self):
        from zope.interface.verify import verifyObject

        from ..interfaces.events import IPrincipalCreatedEvent
        verifyObject(IPrincipalCreatedEvent, self._makeOne())


class PrincipalDeletedTests(unittest.TestCase, ConformsToIPASEvent):

    def _getTargetClass(self):
        from ..events import PrincipalDeleted
        return PrincipalDeleted

    def _makeOne(self, principal=None):
        if principal is None:
            principal = DummyPrincipal()
        return self._getTargetClass()(principal)

    def test_class_conforms_to_IPrincipalDeletedEvent(self):
        from zope.interface.verify import verifyClass

        from ..interfaces.events import IPrincipalDeletedEvent
        verifyClass(IPrincipalDeletedEvent, self._getTargetClass())

    def test_instance_conforms_to_IPrincipalDeletedEvent(self):
        from zope.interface.verify import verifyObject

        from ..interfaces.events import IPrincipalDeletedEvent
        verifyObject(IPrincipalDeletedEvent, self._makeOne())


class CredentialsUpdatedTests(unittest.TestCase, ConformsToIPASEvent):

    def _getTargetClass(self):
        from ..events import CredentialsUpdated
        return CredentialsUpdated

    def _makeOne(self, principal=None, password='password'):
        if principal is None:
            principal = DummyPrincipal()
        return self._getTargetClass()(principal, password)

    def test_class_conforms_to_ICredentialsUpdatedEvent(self):
        from zope.interface.verify import verifyClass

        from ..interfaces.events import ICredentialsUpdatedEvent
        verifyClass(ICredentialsUpdatedEvent, self._getTargetClass())

    def test_instance_conforms_to_ICredentialsUpdatedEvent(self):
        from zope.interface.verify import verifyObject

        from ..interfaces.events import ICredentialsUpdatedEvent
        verifyObject(ICredentialsUpdatedEvent, self._makeOne())


class PropertiesUpdatedTests(unittest.TestCase, ConformsToIPASEvent):

    def _getTargetClass(self):
        from ..events import PropertiesUpdated
        return PropertiesUpdated

    def _makeOne(self, principal=None, properties=None):
        if principal is None:
            principal = DummyPrincipal()
        if properties is None:
            properties = {}
        return self._getTargetClass()(principal, properties)

    def test_class_conforms_to_IPropertiesUpdatedEvent(self):
        from zope.interface.verify import verifyClass

        from ..interfaces.events import IPropertiesUpdatedEvent
        verifyClass(IPropertiesUpdatedEvent, self._getTargetClass())

    def test_instance_conforms_to_IPropertiesUpdatedEvent(self):
        from zope.interface.verify import verifyObject

        from ..interfaces.events import IPropertiesUpdatedEvent
        verifyObject(IPropertiesUpdatedEvent, self._makeOne())


class DummyPrincipal(object):
    pass


class GroupCreatedTests(unittest.TestCase, ConformsToIPASEvent):

    def _getTargetClass(self):
        from ..events import GroupCreated
        return GroupCreated

    def _makeOne(self, Group=None):
        if Group is None:
            Group = DummyGroup()
        return self._getTargetClass()(Group, None)

    def test_class_conforms_to_IGroupCreatedEvent(self):
        from zope.interface.verify import verifyClass

        from ..interfaces.events import IGroupCreatedEvent
        verifyClass(IGroupCreatedEvent, self._getTargetClass())

    def test_instance_conforms_to_IGroupCreatedEvent(self):
        from zope.interface.verify import verifyObject

        from ..interfaces.events import IGroupCreatedEvent
        verifyObject(IGroupCreatedEvent, self._makeOne())


class GroupDeletedTests(unittest.TestCase, ConformsToIPASEvent):

    def _getTargetClass(self):
        from ..events import GroupDeleted
        return GroupDeleted

    def _makeOne(self, Group=None):
        if Group is None:
            Group = DummyGroup()
        return self._getTargetClass()(Group)

    def test_class_conforms_to_IGroupDeletedEvent(self):
        from zope.interface.verify import verifyClass

        from ..interfaces.events import IGroupDeletedEvent
        verifyClass(IGroupDeletedEvent, self._getTargetClass())

    def test_instance_conforms_to_IGroupDeletedEvent(self):
        from zope.interface.verify import verifyObject

        from ..interfaces.events import IGroupDeletedEvent
        verifyObject(IGroupDeletedEvent, self._makeOne())


class PrincipalAddedToGroupTests(unittest.TestCase, ConformsToIPASEvent):

    def _getTargetClass(self):
        from ..events import PrincipalAddedToGroup
        return PrincipalAddedToGroup

    def _makeOne(self, principal=None, group_id=None):
        if principal is None:
            principal = DummyPrincipal()
        if group_id is None:
            group_id = 'testgroup'
        return self._getTargetClass()(principal, group_id)

    def test_class_conforms_to_IPrincipalAddedToGroupEvent(self):
        from zope.interface.verify import verifyClass

        from ..interfaces.events import IPrincipalAddedToGroupEvent
        verifyClass(IPrincipalAddedToGroupEvent, self._getTargetClass())

    def test_instance_conforms_to_IPrincipalAddedToGroupEvent(self):
        from zope.interface.verify import verifyObject

        from ..interfaces.events import IPrincipalAddedToGroupEvent
        verifyObject(IPrincipalAddedToGroupEvent, self._makeOne())

    def test_instantiation(self):
        evt = self._makeOne(group_id='foo')
        self.assertEqual(evt.group_id, 'foo')


class PrincipalRemovedFromGroupTests(unittest.TestCase, ConformsToIPASEvent):

    def _getTargetClass(self):
        from ..events import PrincipalRemovedFromGroup
        return PrincipalRemovedFromGroup

    def _makeOne(self, principal=None, group_id=None):
        if principal is None:
            principal = DummyPrincipal()
        if group_id is None:
            group_id = 'testgroup'
        return self._getTargetClass()(principal, group_id)

    def test_class_conforms_to_IPrincipalRemovedFromGroupEvent(self):
        from zope.interface.verify import verifyClass

        from ..interfaces.events import IPrincipalRemovedFromGroupEvent
        verifyClass(IPrincipalRemovedFromGroupEvent, self._getTargetClass())

    def test_instance_conforms_to_IPrincipalRemovedFromGroupEvent(self):
        from zope.interface.verify import verifyObject

        from ..interfaces.events import IPrincipalRemovedFromGroupEvent
        verifyObject(IPrincipalRemovedFromGroupEvent, self._makeOne())

    def test_instantiation(self):
        evt = self._makeOne(group_id='foo')
        self.assertEqual(evt.group_id, 'foo')


class DummyGroup(object):
    pass
