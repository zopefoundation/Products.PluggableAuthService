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
""" Classes: ZODBUserManager
"""
import copy
import logging

import six

from AccessControl import AuthEncoding
from AccessControl import ClassSecurityInfo
from AccessControl.class_init import InitializeClass
from AccessControl.requestmethod import postonly
from AccessControl.SecurityManagement import getSecurityManager
from BTrees.OOBTree import OOBTree
from OFS.Cache import Cacheable
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from zope.interface import Interface

from Products.PluggableAuthService.interfaces.plugins import \
    IAuthenticationPlugin
from Products.PluggableAuthService.interfaces.plugins import IUserAdderPlugin
from Products.PluggableAuthService.interfaces.plugins import \
    IUserEnumerationPlugin
from Products.PluggableAuthService.permissions import ManageUsers
from Products.PluggableAuthService.permissions import SetOwnPassword
from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin
from Products.PluggableAuthService.utils import classImplements
from Products.PluggableAuthService.utils import createViewName
from Products.PluggableAuthService.utils import csrf_only


try:
    from hashlib import sha1 as sha
except ImportError:
    from sha import sha


logger = logging.getLogger('PluggableAuthService')


class IZODBUserManager(Interface):
    """ Marker interface.
    """


manage_addZODBUserManagerForm = PageTemplateFile(
    'www/zuAdd', globals(), __name__='manage_addZODBUserManagerForm')


def addZODBUserManager(dispatcher, id, title=None, REQUEST=None):
    """ Add a ZODBUserManager to a Pluggable Auth Service. """

    zum = ZODBUserManager(id, title)
    dispatcher._setObject(zum.getId(), zum)

    if REQUEST is not None:
        REQUEST['RESPONSE'].redirect('%s/manage_workspace'
                                     '?manage_tabs_message='
                                     'ZODBUserManager+added.' %
                                     dispatcher.absolute_url())


class ZODBUserManager(BasePlugin, Cacheable):

    """ PAS plugin for managing users in the ZODB.
    """

    meta_type = 'ZODB User Manager'
    zmi_icon = 'fas fa-user'

    security = ClassSecurityInfo()

    def __init__(self, id, title=None):

        self._id = self.id = id
        self.title = title

        self._user_passwords = OOBTree()
        self._login_to_userid = OOBTree()
        self._userid_to_login = OOBTree()

    #
    #   IAuthenticationPlugin implementation
    #
    @security.private
    def authenticateCredentials(self, credentials):

        """ See IAuthenticationPlugin.

        o We expect the credentials to be those returned by
          ILoginPasswordExtractionPlugin.
        """
        login = credentials.get('login')
        password = credentials.get('password')

        if login is None or password is None:
            return None

        # Do we have a link between login and userid?  Do NOT fall
        # back to using the login as userid when there is no match, as
        # that gives a high chance of seeming to log in successfully,
        # but in reality failing.
        userid = self._login_to_userid.get(login)
        if userid is None:
            # Someone may be logging in with a userid instead of a
            # login name and the two are not the same.  We could try
            # turning those around, but really we should just fail.
            #
            # userid = login
            # login = self._userid_to_login.get(userid)
            # if login is None:
            #     return None
            return None

        reference = self._user_passwords.get(userid)

        if reference is None:
            return None

        if AuthEncoding.is_encrypted(reference):
            if AuthEncoding.pw_validate(reference, password):
                return userid, login

        # Support previous naive behavior
        if isinstance(password, six.text_type):
            password = password.encode('utf8')
        digested = sha(password).hexdigest()

        if reference == digested:
            return userid, login

        return None

    #
    #   IUserEnumerationPlugin implementation
    #
    @security.private
    def enumerateUsers(self, id=None, login=None, exact_match=False,
                       sort_by=None, max_results=None, **kw):

        """ See IUserEnumerationPlugin.
        """
        user_info = []
        user_ids = []
        plugin_id = self.getId()
        view_name = createViewName('enumerateUsers', id or login)

        if isinstance(id, six.string_types):
            id = [id]

        if isinstance(login, six.string_types):
            login = [login]

        # Look in the cache first...
        keywords = copy.deepcopy(kw)
        keywords.update({'id': id, 'login': login,
                         'exact_match': exact_match, 'sort_by': sort_by,
                         'max_results': max_results})
        cached_info = self.ZCacheable_get(view_name=view_name,
                                          keywords=keywords, default=None)
        if cached_info is not None:
            return tuple(cached_info)

        terms = id or login

        if exact_match:
            if terms:

                if id:
                    # if we're doing an exact match based on id, it
                    # absolutely will have been qualified (if we have a
                    # prefix), so we can ignore any that don't begin with
                    # our prefix
                    id = [x for x in id if x.startswith(self.prefix)]
                    user_ids.extend([x[len(self.prefix):] for x in id])
                elif login:
                    user_ids.extend([self._login_to_userid.get(x)
                                     for x in login])

                # we're claiming an exact match search, if we still don't
                # have anything, better bail.
                if not user_ids:
                    return ()
            else:
                # insane - exact match with neither login nor id
                return ()

        if user_ids:
            user_filter = None

        else:   # Searching
            user_ids = self.listUserIds()
            user_filter = _ZODBUserFilter(id, login, **kw)

        for user_id in user_ids:

            if self._userid_to_login.get(user_id):
                e_url = '%s/manage_users' % self.getId()
                qs = 'user_id=%s' % user_id

                info = {'id': self.prefix + user_id,
                        'login': self._userid_to_login[user_id],
                        'pluginid': plugin_id,
                        'editurl': '%s?%s' % (e_url, qs)}

                if not user_filter or user_filter(info):
                    user_info.append(info)

        # Put the computed value into the cache
        self.ZCacheable_set(user_info, view_name=view_name, keywords=keywords)

        return tuple(user_info)

    #
    #   IUserAdderPlugin implementation
    #
    @security.private
    def doAddUser(self, login, password):
        try:
            self.addUser(login, login, password)
        except KeyError:
            return False
        return True

    #
    #   (notional)IZODBUserManager interface
    #
    @security.protected(ManageUsers)
    def listUserIds(self):

        """ -> (user_id_1, ... user_id_n)
        """
        return self._user_passwords.keys()

    @security.protected(ManageUsers)
    def getUserInfo(self, user_id):

        """ user_id -> dict
        """
        return {'user_id': user_id,
                'login_name': self._userid_to_login[user_id],
                'pluginid': self.getId()}

    @security.protected(ManageUsers)
    def listUserInfo(self):

        """ -> (dict, ...dict)

        o Return one mapping per user, with the following keys:

          - 'user_id'
          - 'login_name'
        """
        return [self.getUserInfo(x) for x in self._user_passwords.keys()]

    @security.protected(ManageUsers)
    def getUserIdForLogin(self, login_name):

        """ login_name -> user_id

        o Raise KeyError if no user exists for the login name.
        """
        return self._login_to_userid[login_name]

    @security.protected(ManageUsers)
    def getLoginForUserId(self, user_id):

        """ user_id -> login_name

        o Raise KeyError if no user exists for that ID.
        """
        return self._userid_to_login[user_id]

    @security.private
    def addUser(self, user_id, login_name, password):

        if self._user_passwords.get(user_id) is not None:
            raise KeyError('Duplicate user ID: %s' % user_id)

        if self._login_to_userid.get(login_name) is not None:
            raise KeyError('Duplicate login name: %s' % login_name)

        self._user_passwords[user_id] = self._pw_encrypt(password)
        self._login_to_userid[login_name] = user_id
        self._userid_to_login[user_id] = login_name

        # enumerateUsers return value has changed
        view_name = createViewName('enumerateUsers')
        self.ZCacheable_invalidate(view_name=view_name)

    @security.private
    def updateUser(self, user_id, login_name):

        # The following raises a KeyError if the user_id is invalid
        old_login = self.getLoginForUserId(user_id)

        if old_login != login_name:

            if self._login_to_userid.get(login_name) is not None:
                raise ValueError('Login name not available: %s' % login_name)

            del self._login_to_userid[old_login]
            self._login_to_userid[login_name] = user_id
            self._userid_to_login[user_id] = login_name
        # Signal success.
        return True

    @security.private
    def updateEveryLoginName(self, quit_on_first_error=True):
        # Update all login names to their canonical value.  This
        # should be done after changing the login_transform property
        # of pas.  You can set quit_on_first_error to False to report
        # all errors before quitting with an error.  This can be
        # useful if you want to know how many problems there are, if
        # any.
        pas = self._getPAS()
        transform = pas._get_login_transform_method()
        if not transform:
            logger.warning('PAS has a non-existing, empty or wrong '
                           'login_transform property.')
            return

        # Make a fresh mapping, as we do not want to add or remove
        # items to the original mapping while we are iterating over
        # it.
        new_login_to_userid = OOBTree()
        errors = []
        for old_login_name, user_id in self._login_to_userid.items():
            new_login_name = transform(old_login_name)
            if new_login_name in new_login_to_userid:
                logger.error('User id %s: login name %r already taken.',
                             user_id, new_login_name)
                errors.append(new_login_name)
                if quit_on_first_error:
                    break
            new_login_to_userid[new_login_name] = user_id
            if new_login_name != old_login_name:
                self._userid_to_login[user_id] = new_login_name
                # Also, remove from the cache
                view_name = createViewName('enumerateUsers', user_id)
                self.ZCacheable_invalidate(view_name=view_name)
                logger.debug('User id %s: changed login name from %r to %r.',
                             user_id, old_login_name, new_login_name)

        # If there were errors, we do not want to save any changes.
        if errors:
            logger.error('There were %d errors when updating login names. '
                         'quit_on_first_error was %r', len(errors),
                         quit_on_first_error)
            # Make sure the exception we raise is not swallowed.
            self._dont_swallow_my_exceptions = True
            raise ValueError('Transformed login names are not unique: %s.' %
                             ', '.join(errors))

        # Make sure we did not lose any users.
        assert(len(self._login_to_userid.keys())
               == len(new_login_to_userid.keys()))
        # Empty the main cache.
        view_name = createViewName('enumerateUsers')
        self.ZCacheable_invalidate(view_name=view_name)
        # Store the new login mapping.
        self._login_to_userid = new_login_to_userid

    @security.private
    def removeUser(self, user_id):

        if self._user_passwords.get(user_id) is None:
            raise KeyError('Invalid user ID: %s' % user_id)

        login_name = self._userid_to_login[user_id]

        del self._user_passwords[user_id]
        del self._login_to_userid[login_name]
        del self._userid_to_login[user_id]

        # Also, remove from the cache
        view_name = createViewName('enumerateUsers')
        self.ZCacheable_invalidate(view_name=view_name)
        view_name = createViewName('enumerateUsers', user_id)
        self.ZCacheable_invalidate(view_name=view_name)

    @security.private
    def updateUserPassword(self, user_id, password):

        if self._user_passwords.get(user_id) is None:
            raise KeyError('Invalid user ID: %s' % user_id)

        if password:
            self._user_passwords[user_id] = self._pw_encrypt(password)

    @security.private
    def _pw_encrypt(self, password):
        """Returns the AuthEncoding encrypted password

        If 'password' is already encrypted, it is returned
        as is and not encrypted again.
        """
        if AuthEncoding.is_encrypted(password):
            return password
        return AuthEncoding.pw_encrypt(password)

    #
    #   ZMI
    #
    manage_options = (({'label': 'Users', 'action': 'manage_users'},)
                      + BasePlugin.manage_options
                      + Cacheable.manage_options)

    security.declarePublic('manage_widgets')  # NOQA: D001
    manage_widgets = PageTemplateFile('www/zuWidgets', globals(),
                                      __name__='manage_widgets')

    security.declareProtected(ManageUsers, 'manage_users')  # NOQA: D001
    manage_users = PageTemplateFile('www/zuUsers', globals(),
                                    __name__='manage_users')

    @security.protected(ManageUsers)
    @csrf_only
    @postonly
    def manage_addUser(self, user_id, login_name, password, confirm,
                       RESPONSE=None, REQUEST=None):
        """ Add a user via the ZMI.
        """
        if password != confirm:
            message = 'password+and+confirm+do+not+match'

        else:

            if not login_name:
                login_name = user_id

            # ???:  validate 'user_id', 'login_name' against policies?

            self.addUser(user_id, login_name, password)

            message = 'User+added'

        if RESPONSE is not None:
            RESPONSE.redirect('%s/manage_users?manage_tabs_message=%s' %
                              (self.absolute_url(), message))

    @security.protected(ManageUsers)
    @csrf_only
    @postonly
    def manage_updateUserPassword(self, user_id, password, confirm,
                                  RESPONSE=None, REQUEST=None):
        """ Update a user's login name / password via the ZMI.
        """
        if password and password != confirm:
            message = 'password+and+confirm+do+not+match'

        else:

            self.updateUserPassword(user_id, password)

            message = 'password+updated'

        if RESPONSE is not None:
            RESPONSE.redirect('%s/manage_users?manage_tabs_message=%s' %
                              (self.absolute_url(), message))

    @security.protected(ManageUsers)
    @csrf_only
    @postonly
    def manage_updateUser(self, user_id, login_name, RESPONSE=None,
                          REQUEST=None):
        """ Update a user's login name via the ZMI.
        """
        if not login_name:
            login_name = user_id

        # ???:  validate 'user_id', 'login_name' against policies?

        self.updateUser(user_id, login_name)

        message = 'Login+name+updated'

        if RESPONSE is not None:
            RESPONSE.redirect('%s/manage_users?manage_tabs_message=%s' %
                              (self.absolute_url(), message))

    @security.protected(ManageUsers)
    @csrf_only
    @postonly
    def manage_removeUsers(self, user_ids, RESPONSE=None, REQUEST=None):
        """ Remove one or more users via the ZMI.
        """
        user_ids = filter(None, user_ids)

        if not user_ids:
            message = 'no+users+selected'

        else:

            for user_id in user_ids:
                self.removeUser(user_id)

            message = 'Users+removed'

        if RESPONSE is not None:
            RESPONSE.redirect('%s/manage_users?manage_tabs_message=%s' %
                              (self.absolute_url(), message))

    #
    #   Allow users to change their own login name and password.
    #
    @security.protected(SetOwnPassword)
    def getOwnUserInfo(self):

        """ Return current user's info.
        """
        user_id = getSecurityManager().getUser().getId()

        return self.getUserInfo(user_id)

    security.declareProtected(SetOwnPassword,  # NOQA: D001
                              'manage_updatePasswordForm')
    manage_updatePasswordForm = PageTemplateFile(
                                    'www/zuPasswd',
                                    globals(),
                                    __name__='manage_updatePasswordForm')

    @security.protected(SetOwnPassword)
    @csrf_only
    @postonly
    def manage_updatePassword(self, login_name, password, confirm,
                              RESPONSE=None, REQUEST=None):
        """ Update the current user's password and login name.
        """
        user_id = getSecurityManager().getUser().getId()
        if password != confirm:
            message = 'password+and+confirm+do+not+match'

        else:

            if not login_name:
                login_name = user_id

            # ???:  validate 'user_id', 'login_name' against policies?
            self.updateUser(user_id, login_name)
            self.updateUserPassword(user_id, password)

            message = 'password+updated'

        if RESPONSE is not None:
            RESPONSE.redirect('%s/manage_updatePasswordForm'
                              '?manage_tabs_message=%s' %
                              (self.absolute_url(), message))


classImplements(ZODBUserManager, IZODBUserManager, IAuthenticationPlugin,
                IUserEnumerationPlugin, IUserAdderPlugin)

InitializeClass(ZODBUserManager)


class _ZODBUserFilter:

    def __init__(self, id=None, login=None, **kw):

        self._filter_ids = id
        self._filter_logins = login
        self._filter_keywords = kw

    def __call__(self, user_info):

        if self._filter_ids:

            key = 'id'
            to_test = self._filter_ids

        elif self._filter_logins:

            key = 'login'
            to_test = self._filter_logins

        elif self._filter_keywords:
            return 0    # ???:  try using 'kw'

        else:
            return 1    # the search is done without any criteria

        value = user_info.get(key)

        if not value:
            return 0

        for contained in to_test:
            if value.lower().find(contained.lower()) >= 0:
                return 1

        return 0
