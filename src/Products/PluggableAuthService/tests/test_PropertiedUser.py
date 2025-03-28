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
import unittest

from Acquisition import Implicit

from .conformance import IBasicUser_conformance
from .conformance import IPropertiedUser_conformance


def faux_method(self, x):
    """Just a faux function object with local roles defined later."""


faux_method.__ac_local_roles__ = {'Group C': ('Manager', 'Owner')}


class FauxProtected(Implicit):

    def __init__(self, local_roles=()):

        self.__ac_local_roles__ = local_roles


class PropertiedUserTests(unittest.TestCase, IBasicUser_conformance,
                          IPropertiedUser_conformance):

    def _getTargetClass(self):

        from ..PropertiedUser import PropertiedUser

        return PropertiedUser

    def _makeOne(self, id='testing', login=None, *args, **kw):

        return self._getTargetClass()(id, login, *args, **kw)

    def test_empty(self):

        user = self._makeOne('empty')

        # BaseUser interface
        self.assertEqual(user.getId(), 'empty')
        self.assertEqual(user.getUserName(), 'empty')
        self.assertRaises(NotImplementedError, user._getPassword)
        self.assertEqual(len(user.getRoles()), 0)
        self.assertEqual(len(user.getGroups()), 0)
        self.assertEqual(len(user.getDomains()), 0)

        # plus propertysheets
        self.assertEqual(len(user.listPropertysheets()), 0)
        self.assertRaises(KeyError, user.getPropertysheet, 'nonesuch')

    def test_groups(self):
        groups = ('Group A', 'Group B')
        user = self._makeOne('groups')
        user._addGroups(groups)
        self.assertEqual(len(user.getGroups()), len(groups))
        for g in user.getGroups():
            self.assertIn(g, groups)

    def test_username(self):
        user = self._makeOne('username', 'User with Username')
        self.assertEqual(user.getUserName(), 'User with Username')

    def test_roles(self):
        roles = ['Manager', 'Members']
        user = self._makeOne('user')
        user._addRoles(roles)
        self.assertEqual(len(user.getRoles()), 2)
        for r in user.getRoles():
            self.assertIn(r, roles)

    def test_addPropertysheet(self):

        user = self._makeOne()

        user.addPropertysheet('one', {'a': 0, 'b': 'jabber'})

        ids = user.listPropertysheets()

        self.assertEqual(len(ids), 1)
        self.assertEqual(ids[0], 'one')

        sheet = user.getPropertysheet('one')

        self.assertEqual(len(sheet.propertyMap()), 2)
        self.assertEqual(sheet.getPropertyType('a'), 'int')
        self.assertEqual(sheet.getPropertyType('b'), 'string')
        self.assertEqual(sheet.getId(), 'one')

        sheet = user['one']

        self.assertEqual(len(sheet.propertyMap()), 2)
        self.assertEqual(sheet.getPropertyType('a'), 'int')
        self.assertEqual(sheet.getPropertyType('b'), 'string')

        self.assertRaises(KeyError, user.getPropertysheet, 'another')

    def test_getRolesInContext_no_local(self):

        groups = ('Group A', 'Group B')
        user = self._makeOne()
        user._addGroups(groups)

        self.assertEqual(len(user.getRoles()), 0)
        self.assertEqual(len(user.getGroups()), len(groups))

        faux = FauxProtected()

        local_roles = user.getRolesInContext(faux)
        self.assertEqual(len(local_roles), 0)

    def test_getRolesInContext_group_match(self):

        groups = ('Group A', 'Group B')
        user = self._makeOne()
        user._addGroups(groups)

        faux = FauxProtected({'Group A': ('Manager',)})

        local_roles = user.getRolesInContext(faux)
        self.assertEqual(len(local_roles), 1)
        self.assertIn('Manager', local_roles)

    def test_getRolesInContext_group_overlap(self):

        groups = ('Group A', 'Group B')
        user = self._makeOne()
        user._addGroups(groups)

        faux = FauxProtected({'Group A': ('Manager',),
                              'Group B': ('Manager', 'Owner')})

        local_roles = user.getRolesInContext(faux)
        self.assertEqual(len(local_roles), 2)
        self.assertIn('Manager', local_roles)
        self.assertIn('Owner', local_roles)

    def test_getRolesInContext_group_nomatch(self):

        groups = ('Group A', 'Group B')
        user = self._makeOne()
        user._addGroups(groups)

        faux = FauxProtected({'Group C': ('Manager',)})

        local_roles = user.getRolesInContext(faux)
        self.assertEqual(len(local_roles), 0)

    def test_getRolesInContext_acquisition(self):

        groups = ('Group A', 'Group B')
        user = self._makeOne()
        user._addGroups(groups)

        faux_container = FauxProtected({'Group A': ('Manager',)})
        unwrapped_contained = FauxProtected({'Group C': ('Manager', 'Owner')})
        faux_contained = unwrapped_contained.__of__(faux_container)

        local_roles = user.getRolesInContext(faux_contained)
        self.assertEqual(len(local_roles), 1)
        self.assertIn('Manager', local_roles)

    def test_getRolesInContext_weslayan(self):

        # Test "methodish" checks.

        groups = ('Group A', 'Group B')
        user = self._makeOne()
        user._addGroups(groups)

        FauxProtected.method = faux_method
        faux_self = FauxProtected({'Group A': ('Manager',)})

        local_roles = user.getRolesInContext(faux_self.method)
        self.assertEqual(len(local_roles), 1)
        self.assertIn('Manager', local_roles)

    def test_allowed_not_even_god_should(self):

        from AccessControl.PermissionRole import _what_not_even_god_should_do
        user = self._makeOne()

        self.assertFalse(user.allowed(None, _what_not_even_god_should_do))

    def test_allowed_anonymous(self):

        user = self._makeOne()

        self.assertTrue(user.allowed(None, ('Anonymous',)))

    def test_allowed_authenticated(self):

        user = self._makeOne()

        self.assertTrue(user.allowed(None, ('Authenticated',)))

    def test_allowed_authenticated_required_but_anonymous(self):

        user = self._makeOne('Anonymous User')

        self.assertFalse(user.allowed(None, ('Authenticated',)))

    def test_allowed_global_roles_ok(self):

        user = self._makeOne()
        user._addRoles(('Role 1', 'Role 2'))

        self.assertTrue(user.allowed(None, ('Role 1',)))

    def test_allowed_global_roles_not_ok(self):

        user = self._makeOne()
        user._addRoles(('Role 1', 'Role 2'))

        self.assertFalse(user.allowed(None, ('Role 3',)))

    def test_allowed_local_roles_on_user_ok(self):

        user = self._makeOne('user')
        object = FauxProtected({'user': ('Role 1',)})

        self.assertTrue(user.allowed(object, ('Role 1',)))

    def test_allowed_local_roles_on_user_not_ok(self):

        user = self._makeOne('user')
        object = FauxProtected({'user': ('Role 1',)})

        self.assertFalse(user.allowed(object, ('Role 2',)))

    def test_allowed_local_roles_on_group_ok(self):

        user = self._makeOne('user')
        user._addGroups(('Group 1', 'Group 2'))
        object = FauxProtected({'Group 1': ('Role 1',)})

        self.assertTrue(user.allowed(object, ('Role 1',)))

    def test_allowed_acquisition(self):

        groups = ('Group A', 'Group B')
        user = self._makeOne()
        user._addGroups(groups)

        faux_container = FauxProtected({'Group A': ('Manager',)})
        unwrapped_contained = FauxProtected({'Group C': ('Manager', 'Owner')})
        faux_contained = unwrapped_contained.__of__(faux_container)

        self.assertTrue(user.allowed(faux_contained, ('Manager',)))

    def test_allowed_weslayan(self):

        # Test "methodish" checks.

        groups = ('Group A', 'Group B')
        user = self._makeOne()
        user._addGroups(groups)

        FauxProtected.method = faux_method
        faux_self = FauxProtected({'Group A': ('Manager',)})

        self.assertTrue(user.allowed(faux_self.method, ('Manager',)))
