##############################################################################
#
# Copyright (c) 2001-2008 Zope Foundation and Contributors
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
from AccessControl.AuthEncoding import pw_encrypt
from Products.PluggableAuthService.plugins.tests.helpers \
    import makeRequestAndResponse
from Products.PluggableAuthService.tests import conformance
from zExceptions import Forbidden
import unittest


class DummyUser:

    def __init__(self, id):
        self._id = id

    def getId(self):
        return self._id


class FakePAS(object):

    def _get_login_transform_method(self):
        return None

    def applyTransform(self, value):
        return value


class FakeLowerCasePAS(object):

    def _get_login_transform_method(self):
        return self.lower

    def lower(self, value):
        return value.lower()

    def applyTransform(self, value):
        return value.lower()


class ZODBUserManagerTests(
    unittest.TestCase,
    conformance.IAuthenticationPlugin_conformance,
    conformance.IUserEnumerationPlugin_conformance,
    conformance.IUserAdderPlugin_conformance
):

    def _getTargetClass(self):

        from Products.PluggableAuthService.plugins.ZODBUserManager \
            import ZODBUserManager

        return ZODBUserManager

    def _makeOne(self, id='test', *args, **kw):

        return self._getTargetClass()(id=id, *args, **kw)

    def test_empty(self):

        zum = self._makeOne()

        self.assertEqual(len(zum.listUserIds()), 0)
        self.assertEqual(len(zum.enumerateUsers()), 0)
        self.assertRaises(
            KeyError,
            zum.getUserIdForLogin,
            'userid@example.com')
        self.assertRaises(KeyError, zum.getLoginForUserId, 'userid')

    def test_addUser(self):

        zum = self._makeOne()

        zum.addUser('userid', 'userid@example.com', 'password')

        user_ids = zum.listUserIds()
        self.assertEqual(len(user_ids), 1)
        self.assertEqual(user_ids[0], 'userid')
        self.assertEqual(zum.getUserIdForLogin('userid@example.com'), 'userid')
        self.assertEqual(zum.getLoginForUserId('userid'), 'userid@example.com')

        info_list = zum.enumerateUsers()
        self.assertEqual(len(info_list), 1)
        info = info_list[0]
        self.assertEqual(info['id'], 'userid')
        self.assertEqual(info['login'], 'userid@example.com')

    def test_addUser_duplicate_check(self):

        zum = self._makeOne()

        zum.addUser('userid', 'userid@example.com', 'password')

        self.assertRaises(
            KeyError,
            zum.addUser,
            'userid',
            'luser@other.com',
            'wordpass')

        self.assertRaises(
            KeyError,
            zum.addUser,
            'new_user',
            'userid@example.com',
            '3733t')

    def test_removeUser_nonesuch(self):

        zum = self._makeOne()

        self.assertRaises(KeyError, zum.removeUser, 'nonesuch')

    def test_removeUser_valid_id(self):

        zum = self._makeOne()

        zum.addUser('userid', 'userid@example.com', 'password')
        zum.addUser('doomed', 'doomed@example.com', 'password')

        zum.removeUser('doomed')

        user_ids = zum.listUserIds()
        self.assertEqual(len(user_ids), 1)
        self.assertEqual(len(zum.enumerateUsers()), 1)
        self.assertEqual(user_ids[0], 'userid')

        self.assertEqual(zum.getUserIdForLogin('userid@example.com'), 'userid')
        self.assertEqual(zum.getLoginForUserId('userid'), 'userid@example.com')

        self.assertRaises(
            KeyError,
            zum.getUserIdForLogin,
            'doomed@example.com')
        self.assertRaises(KeyError, zum.getLoginForUserId, 'doomed')

    def test_authenticateCredentials_bad_creds(self):

        zum = self._makeOne()

        zum.addUser('userid', 'userid@example.com', 'password')

        self.assertEqual(zum.authenticateCredentials({}), None)

    def test_authenticateCredentials_valid_creds(self):

        zum = self._makeOne()

        zum.addUser('userid', 'userid@example.com', 'password')

        user_id, login = zum.authenticateCredentials(
            {'login': 'userid@example.com', 'password': 'password'
             })

        self.assertEqual(user_id, 'userid')
        self.assertEqual(login, 'userid@example.com')

    def test_authenticateCredentials_only_matches_login_name(self):
        # When userid and login name are different, then
        # authentication with the userid should fail.  Alternatively,
        # perhaps it would not be too bad, but we should definitely
        # NOT return the userid as the login name, which was the
        # previous behaviour, as this makes us appear to login but it
        # fails a bit later on anyway.
        zum = self._makeOne()

        zum.addUser('userid', 'userid@example.com', 'password')

        self.assertEqual(zum.authenticateCredentials(
            {'login': 'userid', 'password': 'password'}), None)

    def test_enumerateUsers_no_criteria(self):

        from Products.PluggableAuthService.tests.test_PluggableAuthService \
            import FauxRoot

        root = FauxRoot()
        zum = self._makeOne(id='no_crit').__of__(root)

        ID_LIST = ('foo', 'bar', 'baz', 'bam')

        for id in ID_LIST:

            zum.addUser(id, '%s@example.com' % id, 'password')

        info_list = zum.enumerateUsers()

        self.assertEqual(len(info_list), len(ID_LIST))

        sorted = list(ID_LIST)
        sorted.sort()

        for i in range(len(sorted)):

            self.assertEqual(info_list[i]['id'], sorted[i])
            self.assertEqual(
                info_list[i]['login'],
                '%s@example.com' %
                sorted[i])
            self.assertEqual(info_list[i]['pluginid'], 'no_crit')
            self.assertEqual(
                info_list[i]['editurl'],
                'no_crit/manage_users?user_id=%s' %
                sorted[i])

    def test_enumerateUsers_exact(self):

        from Products.PluggableAuthService.tests.test_PluggableAuthService \
            import FauxRoot

        root = FauxRoot()
        zum = self._makeOne(id='exact').__of__(root)

        ID_LIST = ('foo', 'bar', 'baz', 'bam')

        for id in ID_LIST:

            zum.addUser(id, '%s@example.com' % id, 'password')

        info_list = zum.enumerateUsers(id='bar', exact_match=True)

        self.assertEqual(len(info_list), 1)
        info = info_list[0]

        self.assertEqual(info['id'], 'bar')
        self.assertEqual(info['login'], 'bar@example.com')
        self.assertEqual(info['pluginid'], 'exact')
        self.assertEqual(info['editurl'], 'exact/manage_users?user_id=bar')

    def test_enumerateUsers_partial(self):

        from Products.PluggableAuthService.tests.test_PluggableAuthService \
            import FauxRoot

        root = FauxRoot()
        zum = self._makeOne(id='partial').__of__(root)

        ID_LIST = ('foo', 'bar', 'baz', 'bam')

        for id in ID_LIST:

            zum.addUser(id, '%s@example.com' % id, 'password')

        info_list = zum.enumerateUsers(login='example.com', exact_match=False)

        self.assertEqual(len(info_list), len(ID_LIST))  # all match

        sorted = list(ID_LIST)
        sorted.sort()

        for i in range(len(sorted)):

            self.assertEqual(info_list[i]['id'], sorted[i])
            self.assertEqual(
                info_list[i]['login'],
                '%s@example.com' %
                sorted[i])
            self.assertEqual(info_list[i]['pluginid'], 'partial')
            self.assertEqual(
                info_list[i]['editurl'],
                'partial/manage_users?user_id=%s' %
                sorted[i])

        info_list = zum.enumerateUsers(id='ba', exact_match=False)

        self.assertEqual(len(info_list), len(ID_LIST) - 1)  # no 'foo'

        sorted = list(ID_LIST)
        sorted.sort()

        for i in range(len(sorted) - 1):

            self.assertEqual(info_list[i]['id'], sorted[i])
            self.assertEqual(
                info_list[i]['login'],
                '%s@example.com' %
                sorted[i])
            self.assertEqual(info_list[i]['pluginid'], 'partial')
            self.assertEqual(
                info_list[i]['editurl'],
                'partial/manage_users?user_id=%s' %
                sorted[i])

    def test_enumerateUsers_other_criteria(self):

        from Products.PluggableAuthService.tests.test_PluggableAuthService \
            import FauxRoot

        root = FauxRoot()
        zum = self._makeOne(id='partial').__of__(root)

        ID_LIST = ('foo', 'bar', 'baz', 'bam')

        for id in ID_LIST:

            zum.addUser(id, '%s@example.com' % id, 'password')

        info_list = zum.enumerateUsers(email='bar@example.com',
                                       exact_match=False)
        self.assertEqual(len(info_list), 0)

    def test_enumerateUsers_unicode(self):

        from Products.PluggableAuthService.tests.test_PluggableAuthService \
            import FauxRoot

        root = FauxRoot()
        zum = self._makeOne(id='partial').__of__(root)

        ID_LIST = ('foo', 'bar', 'baz', 'bam')

        for id in ID_LIST:

            zum.addUser(id, '%s@example.com' % id, 'password')

        info_list = zum.enumerateUsers(id=u'abc',
                                       exact_match=False)
        self.assertEqual(len(info_list), 0)

    def test_enumerateUsers_exact_nonesuch(self):

        from Products.PluggableAuthService.tests.test_PluggableAuthService \
            import FauxRoot

        root = FauxRoot()
        zum = self._makeOne(id='exact_nonesuch').__of__(root)

        ID_LIST = ('foo', 'bar', 'baz', 'bam')

        for id in ID_LIST:

            zum.addUser(id, '%s@example.com' % id, 'password')

        self.assertEquals(zum.enumerateUsers(id='qux', exact_match=True), ())

    def test_enumerateUsers_multiple_ids(self):

        from Products.PluggableAuthService.tests.test_PluggableAuthService \
            import FauxRoot

        root = FauxRoot()
        zum = self._makeOne(id='partial').__of__(root)

        ID_LIST = ('foo', 'bar', 'baz', 'bam')

        for id in ID_LIST:

            zum.addUser(id, '%s@example.com' % id, 'password')

        info_list = zum.enumerateUsers(id=ID_LIST)

        self.assertEqual(len(info_list), len(ID_LIST))

        for info in info_list:
            self.failUnless(info['id'] in ID_LIST)

        SUBSET = ID_LIST[:3]

        info_list = zum.enumerateUsers(id=SUBSET)

        self.assertEqual(len(info_list), len(SUBSET))

        for info in info_list:
            self.failUnless(info['id'] in SUBSET)

    def test_enumerateUsers_multiple_logins(self):

        from Products.PluggableAuthService.tests.test_PluggableAuthService \
            import FauxRoot

        root = FauxRoot()
        zum = self._makeOne(id='partial').__of__(root)

        ID_LIST = ('foo', 'bar', 'baz', 'bam')
        LOGIN_LIST = ['%s@example.com' % x for x in ID_LIST]

        for i in range(len(ID_LIST)):

            zum.addUser(ID_LIST[i], LOGIN_LIST[i], 'password')

        info_list = zum.enumerateUsers(login=LOGIN_LIST)

        self.assertEqual(len(info_list), len(LOGIN_LIST))

        for info in info_list:
            self.failUnless(info['id'] in ID_LIST)
            self.failUnless(info['login'] in LOGIN_LIST)

        SUBSET_LOGINS = LOGIN_LIST[:3]
        SUBSET_IDS = ID_LIST[:3]

        info_list = zum.enumerateUsers(login=SUBSET_LOGINS)

        self.assertEqual(len(info_list), len(SUBSET_LOGINS))

        for info in info_list:
            self.failUnless(info['id'] in SUBSET_IDS)
            self.failUnless(info['login'] in SUBSET_LOGINS)

    def test_authenticateWithOldPasswords(self):

        try:
            from hashlib import sha1 as sha
        except:
            from sha import sha

        zum = self._makeOne()

        # synthesize an older account

        old_password = sha('old_password').hexdigest()
        zum._user_passwords['old_user'] = old_password
        zum._login_to_userid['old_user@example.com'] = 'old_user'
        zum._userid_to_login['old_user'] = 'old_user@example.com'

        # create a new user

        zum.addUser('new_user', 'new_user@example.com', 'new_password')

        user_id, login = zum.authenticateCredentials(
            {'login': 'old_user@example.com', 'password': 'old_password'
             })

        self.assertEqual(user_id, 'old_user')
        self.assertEqual(login, 'old_user@example.com')

        user_id, login = zum.authenticateCredentials(
            {'login': 'new_user@example.com', 'password': 'new_password'
             })

        self.assertEqual(user_id, 'new_user')
        self.assertEqual(login, 'new_user@example.com')

    def test_updateUserPassword(self):

        zum = self._makeOne()

        # Create a user and make sure we can authenticate with it
        zum.addUser('user1', 'user1@example.com', 'password')
        info1 = {'login': 'user1@example.com', 'password': 'password'}
        user_id, login = zum.authenticateCredentials(info1)
        self.assertEqual(user_id, 'user1')
        self.assertEqual(login, 'user1@example.com')

        # Give the user a new password; attempting to authenticate with the
        # old password must fail
        zum.updateUserPassword('user1', 'new_password')
        self.failIf(zum.authenticateCredentials(info1))

        # Try to authenticate with the new password, this must succeed.
        info2 = {'login': 'user1@example.com', 'password': 'new_password'}
        user_id, login = zum.authenticateCredentials(info2)
        self.assertEqual(user_id, 'user1')
        self.assertEqual(login, 'user1@example.com')

    def test_updateUser(self):

        zum = self._makeOne()

        # Create a user and make sure we can authenticate with it
        zum.addUser('user1', 'user1@example.com', 'password')
        info1 = {'login': 'user1@example.com', 'password': 'password'}
        user_id, login = zum.authenticateCredentials(info1)
        self.assertEqual(user_id, 'user1')
        self.assertEqual(login, 'user1@example.com')

        # Give the user a new login; attempts to authenticate with the
        # old login must fail.
        zum.updateUser('user1', 'user1@foobar.com')
        self.failIf(zum.authenticateCredentials(info1))

        # Try to authenticate with the new login, this must succeed.
        info2 = {'login': 'user1@foobar.com', 'password': 'password'}
        user_id, login = zum.authenticateCredentials(info2)
        self.assertEqual(user_id, 'user1')
        self.assertEqual(login, 'user1@foobar.com')

    def test_updateUser_login_name_conflicts(self):
        # See https://bugs.launchpad.net/zope-pas/+bug/789858
        zum = self._makeOne()

        # Create a user and make sure we can authenticate with it
        zum.addUser('user1', 'user1@example.com', 'password')
        zum.addUser('user2', 'user2@example.com', 'other')

        self.assertRaises(ValueError,
                          zum.updateUser, 'user1', 'user2@example.com')

    def test_updateEveryLoginName(self):

        zum = self._makeOne()
        zum._getPAS = lambda: FakePAS()

        # Create two users and make sure we can authenticate with it
        zum.addUser('User1', 'User1@Example.Com', 'password')
        zum.addUser('User2', 'User2@Example.Com', 'password')
        info1 = {'login': 'User1@Example.Com', 'password': 'password'}
        info2 = {'login': 'User2@Example.Com', 'password': 'password'}
        user_id, login = zum.authenticateCredentials(info1)
        self.assertEqual(user_id, 'User1')
        self.assertEqual(login, 'User1@Example.Com')
        user_id, login = zum.authenticateCredentials(info2)
        self.assertEqual(user_id, 'User2')
        self.assertEqual(login, 'User2@Example.Com')

        # Give all users a new login, using the applyTransform method
        # of PAS.  There should be no changes.
        zum.updateEveryLoginName()
        self.failUnless(zum.authenticateCredentials(info1))
        self.failUnless(zum.authenticateCredentials(info2))

        # Use a PAS configured to transform login names to lower case.
        zum._getPAS = lambda: FakeLowerCasePAS()

        # Update all login names
        zum.updateEveryLoginName()

        # The old mixed case logins no longer work.  Note that if you
        # query PAS (via the validate or _extractUserIds method), PAS
        # is responsible for transforming the login before passing it
        # to our plugin.
        self.failIf(zum.authenticateCredentials(info1))
        self.failIf(zum.authenticateCredentials(info2))

        # Authentication with all lowercase login works.
        info1 = {'login': 'user1@example.com', 'password': 'password'}
        info2 = {'login': 'user2@example.com', 'password': 'password'}
        user_id, login = zum.authenticateCredentials(info1)
        self.assertEqual(user_id, 'User1')
        self.assertEqual(login, 'user1@example.com')
        user_id, login = zum.authenticateCredentials(info2)
        self.assertEqual(user_id, 'User2')
        self.assertEqual(login, 'user2@example.com')

    def test_enumerateUsersWithOptionalMangling(self):

        zum = self._makeOne()
        zum.prefix = 'special__'

        zum.addUser('user', 'login', 'password')
        info = zum.enumerateUsers(login='login')
        self.assertEqual(info[0]['id'], 'special__user')

    def test_getUserByIdWithOptionalMangling(self):

        zum = self._makeOne()
        zum.prefix = 'special__'

        zum.addUser('user', 'login', 'password')

        info = zum.enumerateUsers(id='user', exact_match=True)
        self.assertEqual(len(info), 0)

        info = zum.enumerateUsers(id='special__user', exact_match=True)
        self.assertEqual(info[0]['id'], 'special__user')

        info = zum.enumerateUsers(id='special__luser', exact_match=True)
        self.assertEqual(len(info), 0)

    def test_addUser_with_not_yet_encrypted_password(self):
        # See collector #1869 && #1926
        from AccessControl.AuthEncoding import is_encrypted

        USER_ID = 'not_yet_encrypted'
        PASSWORD = 'password'

        self.failIf(is_encrypted(PASSWORD))

        zum = self._makeOne()
        zum.addUser(USER_ID, USER_ID, PASSWORD)

        uid_and_info = zum.authenticateCredentials(
            {'login': USER_ID, 'password': PASSWORD
             })

        self.assertEqual(uid_and_info, (USER_ID, USER_ID))

    def test_addUser_with_preencrypted_password(self):
        # See collector #1869 && #1926
        USER_ID = 'already_encrypted'
        PASSWORD = 'password'
        ENCRYPTED = pw_encrypt(PASSWORD)

        zum = self._makeOne()
        zum.addUser(USER_ID, USER_ID, ENCRYPTED)

        uid_and_info = zum.authenticateCredentials(
            {'login': USER_ID, 'password': PASSWORD
             })

        self.assertEqual(uid_and_info, (USER_ID, USER_ID))

    def test_updateUserPassword_with_not_yet_encrypted_password(self):
        from AccessControl.AuthEncoding import is_encrypted

        USER_ID = 'not_yet_encrypted'
        PASSWORD = 'password'

        self.failIf(is_encrypted(PASSWORD))

        zum = self._makeOne()
        zum.addUser(USER_ID, USER_ID, '')
        zum.updateUserPassword(USER_ID, PASSWORD)

        uid_and_info = zum.authenticateCredentials(
            {'login': USER_ID, 'password': PASSWORD
             })

        self.assertEqual(uid_and_info, (USER_ID, USER_ID))

    def test_updateUserPassword_with_preencrypted_password(self):
        USER_ID = 'already_encrypted'
        PASSWORD = 'password'

        ENCRYPTED = pw_encrypt(PASSWORD)

        zum = self._makeOne()
        zum.addUser(USER_ID, USER_ID, '')
        zum.updateUserPassword(USER_ID, ENCRYPTED)

        uid_and_info = zum.authenticateCredentials(
            {'login': USER_ID, 'password': PASSWORD
             })

        self.assertEqual(uid_and_info, (USER_ID, USER_ID))

    def test_manage_updatePassword(self):
        from AccessControl.SecurityManagement import newSecurityManager
        from AccessControl.SecurityManagement import noSecurityManager
        from Acquisition import Implicit
        # Test that a user can update her own password using the
        # ZMI-provided form handler: http://www.zope.org/Collectors/PAS/56
        zum = self._makeOne()

        # Create a user and make sure we can authenticate with it
        zum.addUser('user1', 'user1@example.com', 'password')
        info1 = {'login': 'user1@example.com', 'password': 'password'}
        self.failUnless(zum.authenticateCredentials(info1))

        # Give the user a new password; attempting to authenticate with the
        # old password must fail
        class FauxUser(Implicit):

            def __init__(self, id):
                self._id = id

            def getId(self):
                return self._id

        req, res = makeRequestAndResponse()
        req.set('REQUEST_METHOD', 'POST')
        req.set('method', 'POST')
        req.SESSION = {'_csrft_': 'deadbeef'}
        req.form['csrf_token'] = 'deadbeef'
        newSecurityManager(None, FauxUser('user1'))
        try:
            zum.manage_updatePassword('user2@example.com',
                                      'new_password',
                                      'new_password',
                                      REQUEST=req,
                                      )
        finally:
            noSecurityManager()

        self.failIf(zum.authenticateCredentials(info1))

        # Try to authenticate with the new password, this must succeed.
        info2 = {'login': 'user2@example.com', 'password': 'new_password'}
        user_id, login = zum.authenticateCredentials(info2)
        self.assertEqual(user_id, 'user1')
        self.assertEqual(login, 'user2@example.com')

    def test_manage_updateUserPassword_POST_permissions(self):
        USER_ID = 'testuser'
        PASSWORD = 'password'

        zum = self._makeOne()
        zum.addUser(USER_ID, USER_ID, '')

        req, res = makeRequestAndResponse()
        # Fails with a GET
        req.set('REQUEST_METHOD', 'GET')
        req.set('method', 'GET')
        req.set('SESSION', {})
        self.assertRaises(Forbidden, zum.manage_updateUserPassword,
                          USER_ID, PASSWORD, PASSWORD, REQUEST=req)

        req.set('REQUEST_METHOD', 'POST')
        req.set('method', 'POST')
        self.assertRaises(Forbidden, zum.manage_updateUserPassword,
                          USER_ID, PASSWORD, PASSWORD, REQUEST=req)

        # Works with a POST + CSRF toekn
        req.form['csrf_token'] = 'deadbeef'
        req.SESSION['_csrft_'] = 'deadbeef'
        zum.manage_updateUserPassword(USER_ID, PASSWORD, PASSWORD, REQUEST=req)

    def test_manage_updatePassword_POST_permissions(self):
        from AccessControl.SecurityManagement import newSecurityManager
        from AccessControl.SecurityManagement import noSecurityManager
        from Acquisition import Implicit
        # Give the user a new password; attempting to authenticate with the
        # old password must fail

        class FauxUser(Implicit):

            def __init__(self, id):
                self._id = id

            def getId(self):
                return self._id
        USER_ID = 'testuser'
        PASSWORD = 'password'

        zum = self._makeOne()
        zum.addUser(USER_ID, USER_ID, '')

        req, res = makeRequestAndResponse()
        req.set('REQUEST_METHOD', 'GET')
        req.set('method', 'GET')
        req.set('SESSION', {})
        newSecurityManager(None, FauxUser(USER_ID))
        try:
            self.assertRaises(Forbidden, zum.manage_updatePassword,
                              USER_ID, PASSWORD, PASSWORD, REQUEST=req)

            req.set('REQUEST_METHOD', 'POST')
            req.set('method', 'POST')
            self.assertRaises(Forbidden, zum.manage_updatePassword,
                              USER_ID, PASSWORD, PASSWORD, REQUEST=req)

            # Works with a POST + CSRF toekn
            req.form['csrf_token'] = 'deadbeef'
            req.SESSION['_csrft_'] = 'deadbeef'
            zum.manage_updatePassword(USER_ID, PASSWORD, PASSWORD, REQUEST=req)
        finally:
            noSecurityManager()

    def test_manage_removeUsers_POST_permissions(self):
        USER_ID = 'testuser'

        zum = self._makeOne()
        zum.addUser(USER_ID, USER_ID, '')

        req, res = makeRequestAndResponse()
        req.set('REQUEST_METHOD', 'GET')
        req.set('method', 'GET')
        req.set('SESSION', {})
        self.assertRaises(Forbidden, zum.manage_removeUsers,
                          [USER_ID], REQUEST=req)

        req.set('REQUEST_METHOD', 'POST')
        req.set('method', 'POST')
        self.assertRaises(Forbidden, zum.manage_removeUsers,
                          [USER_ID], REQUEST=req)

        req.form['csrf_token'] = 'deadbeef'
        req.SESSION['_csrft_'] = 'deadbeef'
        zum.manage_removeUsers([USER_ID], REQUEST=req)


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(ZODBUserManagerTests),
    ))
