##############################################################################
#
# Copyright (c) 2006 Zope Foundation and Contributors
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

from six.moves import range

from AccessControl import Unauthorized
from AccessControl.Permissions import add_folders as AddFolders
from AccessControl.Permissions import view as View
from zope import event
from zope.component import adapter
from zope.component import provideHandler
from ZPublisher.utils import basic_auth_encode

from ..events import CredentialsUpdated
from ..events import PASEventNotify
from ..events import userCredentialsUpdatedHandler
from ..interfaces.events import IPrincipalCreatedEvent
from ..PluggableAuthService import PluggableAuthService
from ..tests import pastc


@adapter(IPrincipalCreatedEvent)
def userCreatedHandler(event):
    pas = event.principal.aq_parent
    if not hasattr(pas, 'events'):
        pas.events = []

    pas.events.append(event)


class UserFolderTests(pastc.PASTestCase):

    def afterSetUp(self):
        # Set up roles and a user
        self.uf = self.folder.acl_users
        self.folder._addRole('role1')
        self.folder.manage_role('role1', [View])
        self.uf.roles.addRole('role1')
        self.folder._addRole('role2')
        self.folder.manage_role('role2', [View])
        self.uf.roles.addRole('role2')
        self.uf._doAddUser('user1', 'secret', ['role1'], [])
        # Set up a published object accessible to user
        self.folder.addDTMLMethod('doc', file='the document')
        self.doc = self.folder.doc
        self.doc.manage_permission(View, ['role1'], acquire=0)
        # Rig the REQUEST so it looks like we traversed to doc
        self.app.REQUEST['PUBLISHED'] = self.doc
        self.app.REQUEST['PARENTS'] = [self.app, self.folder]
        self.app.REQUEST.steps = list(self.doc.getPhysicalPath())
        self.basic = basic_auth_encode('user1', 'secret')
        # Make sure we are not logged in
        self.logout()

    def testGetUser(self):
        self.assertNotEqual(self.uf.getUser('user1'), None)

    def testGetBadUser(self):
        self.assertEqual(self.uf.getUser('user2'), None)

    def testGetUserById(self):
        self.assertNotEqual(self.uf.getUserById('user1'), None)

    def testGetBadUserById(self):
        self.assertEqual(self.uf.getUserById('user2'), None)

    @unittest.expectedFailure
    def testGetUsers(self):
        # Fails because of NotImplementedError
        users = self.uf.getUsers()
        self.assertTrue(users)
        self.assertEqual(users[0].getUserName(), 'user1')

    @unittest.expectedFailure
    def testGetUserNames(self):
        # Fails because of NotImplementedError
        names = self.uf.getUserNames()
        self.assertTrue(names)
        self.assertEqual(names[0], 'user1')

    @unittest.expectedFailure
    def testIdentify(self):
        # Fails because of NotImplementedError
        name, password = self.uf.identify(self.basic)
        self.assertEqual(name, 'user1')
        self.assertEqual(password, 'secret')

    def testGetRoles(self):
        user = self.uf.getUser('user1')
        self.assertTrue('role1' in user.getRoles())
        self.assertFalse('role2' in user.getRoles())

    def testGetRolesInContext(self):
        user = self.uf.getUser('user1')
        self.folder.manage_addLocalRoles('user1', ['role2'])
        roles = user.getRolesInContext(self.folder)
        self.assertTrue('role1' in roles)
        self.assertTrue('role2' in roles)

    def testHasRole(self):
        user = self.uf.getUser('user1')
        self.assertTrue(user.has_role('role1', self.folder))

    def testHasLocalRole(self):
        user = self.uf.getUser('user1')
        self.assertFalse(user.has_role('role2', self.folder))
        self.folder.manage_addLocalRoles('user1', ['role2'])
        self.assertTrue(user.has_role('role2', self.folder))

    def testHasPermission(self):
        user = self.uf.getUser('user1')
        self.assertTrue(user.has_permission(View, self.folder))
        self.assertFalse(user.has_permission(AddFolders, self.folder))
        self.folder.manage_role('role1', [AddFolders])
        self.assertTrue(user.has_permission(AddFolders, self.folder))

    def testHasLocalRolePermission(self):
        user = self.uf.getUser('user1')
        self.folder.manage_role('role2', [AddFolders])
        self.assertFalse(user.has_permission(AddFolders, self.folder))
        self.folder.manage_addLocalRoles('user1', ['role2'])
        self.assertTrue(user.has_permission(AddFolders, self.folder))

    @unittest.expectedFailure
    def testAuthenticate(self):
        # Fails because of NotImplementedError
        user = self.uf.getUser('user1')
        self.assertTrue(user.authenticate('secret', self.app.REQUEST))

    def testValidate(self):
        # ???: PAS validate ignores auth argument
        self.app.REQUEST._auth = self.basic
        user = self.uf.validate(self.app.REQUEST, self.basic, ['role1'])
        self.assertNotEqual(user, None)
        self.assertEqual(user.getUserName(), 'user1')

    def testNotValidateWithoutAuth(self):
        # ???: PAS validate ignores auth argument
        user = self.uf.validate(self.app.REQUEST, '', ['role1'])
        self.assertEqual(user, None)

    def testValidateWithoutRoles(self):
        # Note - calling uf.validate without specifying roles will cause
        # the security machinery to determine the needed roles by looking
        # at the object itself (or its container). I'm putting this note
        # in to clarify because the original test expected failure but it
        # really should have expected success, since the user and the
        # object being checked both have the role 'role1', even though no
        # roles are passed explicitly to the userfolder validate method.
        # ???: PAS validate ignores auth argument
        self.app.REQUEST._auth = self.basic
        user = self.uf.validate(self.app.REQUEST, self.basic)
        self.assertEqual(user.getUserName(), 'user1')

    def testNotValidateWithEmptyRoles(self):
        # ???: PAS validate ignores auth argument
        self.app.REQUEST._auth = self.basic
        user = self.uf.validate(self.app.REQUEST, self.basic, [])
        self.assertEqual(user, None)

    def testNotValidateWithWrongRoles(self):
        # ???: PAS validate ignores auth argument
        self.app.REQUEST._auth = self.basic
        user = self.uf.validate(self.app.REQUEST, self.basic, ['role2'])
        self.assertEqual(user, None)

    def testAllowAccessToUser(self):
        self.login('user1')
        try:
            self.folder.restrictedTraverse('doc')
        except Unauthorized:
            self.fail('Unauthorized')

    def testDenyAccessToAnonymous(self):
        self.assertRaises(Unauthorized, self.folder.restrictedTraverse, 'doc')

    def testMaxListUsers(self):
        # create a folder-ish thing which contains a roleManager,
        # then put an acl_users object into the folde-ish thing

        class Folderish(PluggableAuthService):
            def __init__(self, size, count):
                self.maxlistusers = size
                self.users = []
                self.acl_users = self
                self.__allow_groups__ = self
                for i in range(count):
                    self.users.append('Nobody')

            def getUsers(self):
                return self.users

            def user_names(self):
                return self.getUsers()

        tinyFolderOver = Folderish(15, 20)
        tinyFolderUnder = Folderish(15, 10)

        assert tinyFolderOver.maxlistusers == 15
        assert tinyFolderUnder.maxlistusers == 15
        assert len(tinyFolderOver.user_names()) == 20
        assert len(tinyFolderUnder.user_names()) == 10

        with self.assertRaises(OverflowError):
            tinyFolderOver.get_valid_userids()

        try:
            tinyFolderUnder.get_valid_userids()
        except OverflowError:
            self.fail('Raised overflow error erroneously')

    def test__doAddUser_with_not_yet_encrypted_passwords(self):
        # See collector #1869 && #1926
        from AuthEncoding.AuthEncoding import is_encrypted

        USER_ID = 'not_yet_encrypted'
        PASSWORD = 'password'

        self.assertFalse(is_encrypted(PASSWORD))

        self.uf._doAddUser(USER_ID, PASSWORD, [], [])

        uid_and_info = self.uf.users.authenticateCredentials(
            {'login': USER_ID, 'password': PASSWORD})

        self.assertEqual(uid_and_info, (USER_ID, USER_ID))

    def test__doAddUser_with_preencrypted_passwords(self):
        # See collector #1869 && #1926
        from AuthEncoding.AuthEncoding import pw_encrypt

        USER_ID = 'already_encrypted'
        PASSWORD = 'password'

        ENCRYPTED = pw_encrypt(PASSWORD)

        self.uf._doAddUser(USER_ID, ENCRYPTED, [], [])

        uid_and_info = self.uf.users.authenticateCredentials(
            {'login': USER_ID, 'password': PASSWORD})

        self.assertEqual(uid_and_info, (USER_ID, USER_ID))


class UserTests(pastc.PASTestCase):

    def afterSetUp(self):
        self.uf = self.folder.acl_users
        self.uf._doAddUser('chris', '123', ['Manager'], [])
        self.user = self.uf.getUser('chris')

    def testGetUserName(self):
        f = self.user
        self.assertEqual(f.getUserName(), 'chris')

    def testGetUserId(self):
        f = self.user
        self.assertEqual(f.getId(), 'chris')

    def testBaseUserGetIdEqualGetName(self):
        # this is true for the default user type, but will not
        # always be true for extended user types going forward (post-2.6)
        f = self.user
        self.assertEqual(f.getId(), f.getUserName())

    @unittest.expectedFailure
    def testGetPassword(self):
        # fails because of NotImplementedError
        f = self.user
        self.assertEqual(f._getPassword(), '123')

    def testGetRoles(self):
        f = self.user
        self.assertEqual(set(f.getRoles()), {'Authenticated', 'Manager'})

    def testGetDomains(self):
        f = self.user
        self.assertEqual(f.getDomains(), ())


class UserEvents(pastc.PASTestCase):

    def afterSetUp(self):
        # Set up roles and a user
        self.uf = self.folder.acl_users
        self.folder._addRole('role1')
        self.folder.manage_role('role1', [View])
        self.uf.roles.addRole('role1')
        self.folder._addRole('role2')
        self.uf._doAddUser('user1', 'secret', ['role1'], [])

    def testUserCreationEvent(self):
        provideHandler(userCreatedHandler)
        self.uf.events = []

        self.uf._doAddUser('event1', 'secret', ['role1'], [])

        self.assertEqual(len(self.uf.events), 1)
        event = self.uf.events[0]
        self.assertTrue(IPrincipalCreatedEvent.providedBy(event))
        self.assertEqual(event.principal.getUserName(), 'event1')
        self.assertEqual(event.principal.getId(), 'event1')

    def testCredentialsEvent(self):
        import functools
        provideHandler(PASEventNotify)
        provideHandler(userCredentialsUpdatedHandler)

        def wrap(self, *args):
            self._data.append(args)
            return self._original(*args)

        self.uf._data = []
        self.uf._original = self.uf.updateCredentials
        self.uf.updateCredentials = functools.partial(wrap, self.uf)
        self.assertEqual(len(self.uf._data), 0)
        event.notify(CredentialsUpdated(self.uf.getUserById('user_id'),
                                        'testpassword'))
        self.assertEqual(self.uf._data[0][2], 'user_login')
        self.assertEqual(self.uf._data[0][3], 'testpassword')
