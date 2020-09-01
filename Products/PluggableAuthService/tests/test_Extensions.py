##############################################################################
#
# Copyright (c) 2006 Zope Foundation and Contributors
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this
# distribution.
# THIS SOFTWARE IS PROVIDED 'AS IS' AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

from six import StringIO

from ..PluggableAuthService import PluggableAuthService
from ..tests import pastc


class UpgradeTests(pastc.PASTestCase):
    def test_upgrade_pas(self):
        # Test that upgrading acl_users PAS works, or at least does not fail.
        # We had uncaught ImportErrors once.
        from ..Extensions.upgrade import replace_acl_users

        # This is already a PAS, but upgrade still does some stuff.
        uf = self.folder.acl_users
        self.assertIsInstance(uf, PluggableAuthService)

        # Upgrade the folder that contains the acl_users.
        response = StringIO()
        replace_acl_users(self.folder, response)
        uf = self.folder.acl_users
        self.assertIsInstance(uf, PluggableAuthService)

        # Check the messages.
        response.seek(0)
        messages = response.read().splitlines()
        self.assertTrue(messages)
        self.assertEqual(messages[0], 'Already replaced this user folder')
        self.assertEqual(len(messages), 1)

        # Do it again.
        response = StringIO()
        replace_acl_users(self.folder, response)
        uf = self.folder.acl_users
        self.assertIsInstance(uf, PluggableAuthService)
        response.seek(0)
        messages = response.read().splitlines()
        self.assertTrue(messages)
        self.assertEqual(messages[0], 'Already replaced this user folder')
        self.assertEqual(
            messages[1], 'Local role assignments have already been updated.',
        )
        self.assertEqual(len(messages), 2)

    def test_upgrade_userfolder(self):
        # Test that upgrading acl_users user folder works,
        # or at least does not fail.
        # We had uncaught ImportErrors once.
        from OFS.userfolder import UserFolder

        from ..Extensions.upgrade import replace_acl_users

        # Current status
        uf = self.app.acl_users
        self.assertIsInstance(uf, UserFolder)

        # Upgrade the root folder that contains the acl_users.
        response = StringIO()
        replace_acl_users(self.app, response)
        uf = self.app.acl_users
        self.assertIsInstance(uf, PluggableAuthService)

        # Check the messages.
        response.seek(0)
        messages = response.read().splitlines()
        self.assertTrue(messages)
        self.assertEqual(
            messages[0], 'Replaced root acl_users with PluggableAuthService',
        )
        # We could test for this message, but does not seem important.
        # self.assertEqual(
        #     messages[1], '  Ignoring map for unknown principal test_user_1_'
        # )
        self.assertIn('Local Roles map changed for /acl_users', messages)

        # Do it again.
        response = StringIO()
        replace_acl_users(self.app, response)
        uf = self.app.acl_users
        self.assertIsInstance(uf, PluggableAuthService)
        response.seek(0)
        messages = response.read().splitlines()
        self.assertTrue(messages)
        self.assertEqual(messages[0], 'Already replaced this user folder')
        self.assertEqual(
            messages[1], 'Local role assignments have already been updated.',
        )
        self.assertEqual(len(messages), 2)
