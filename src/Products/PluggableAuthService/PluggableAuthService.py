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
""" Classes: PluggableAuthService
"""
import logging

import six

from AccessControl import ClassSecurityInfo
from AccessControl import ModuleSecurityInfo
from AccessControl.class_init import InitializeClass
from AccessControl.Permissions import manage_users as ManageUsers
from AccessControl.SecurityManagement import getSecurityManager
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import noSecurityManager
from AccessControl.users import emergency_user
from AccessControl.users import nobody
from Acquisition import Implicit
from Acquisition import aq_base
from Acquisition import aq_inner
from Acquisition import aq_parent
from OFS.Cache import Cacheable
from OFS.Folder import Folder
from OFS.interfaces import IObjectManager
from OFS.interfaces import IPropertyManager
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from zExceptions import Unauthorized
from zope.event import notify
from ZPublisher import BeforeTraverse
from ZTUtils import Batch

from Products.PluginRegistry.PluginRegistry import PluginRegistry
from Products.StandardCacheManagers.RAMCacheManager import RAMCacheManager

from .events import PrincipalCreated
from .interfaces.authservice import IPluggableAuthService
from .interfaces.authservice import _noroles
from .interfaces.plugins import IAnonymousUserFactoryPlugin
from .interfaces.plugins import IAuthenticationPlugin
from .interfaces.plugins import IChallengePlugin
from .interfaces.plugins import IChallengeProtocolChooser
from .interfaces.plugins import ICredentialsResetPlugin
from .interfaces.plugins import ICredentialsUpdatePlugin
from .interfaces.plugins import IExtractionPlugin
from .interfaces.plugins import IGroupEnumerationPlugin
from .interfaces.plugins import IGroupsPlugin
from .interfaces.plugins import ILoginPasswordHostExtractionPlugin
from .interfaces.plugins import INotCompetentPlugin
from .interfaces.plugins import IPropertiesPlugin
from .interfaces.plugins import IRequestTypeSniffer
from .interfaces.plugins import IRoleAssignerPlugin
from .interfaces.plugins import IRoleEnumerationPlugin
from .interfaces.plugins import IRolesPlugin
from .interfaces.plugins import IUpdatePlugin
from .interfaces.plugins import IUserAdderPlugin
from .interfaces.plugins import IUserEnumerationPlugin
from .interfaces.plugins import IUserFactoryPlugin
from .interfaces.plugins import IValidationPlugin
from .permissions import SearchPrincipals
from .PropertiedUser import PropertiedUser
from .utils import _wwwdir
from .utils import classImplements
from .utils import createKeywords
from .utils import createViewName
from .utils import url_local


security = ModuleSecurityInfo(
    'Products.PluggableAuthService.PluggableAuthService')

logger = logging.getLogger('PluggableAuthService')

#   Errors which plugins may raise, and which we suppress:
_SWALLOWABLE_PLUGIN_EXCEPTIONS = (NameError, AttributeError, KeyError,
                                  TypeError, ValueError)


# except if they tell us not to do so
def reraise(plugin):
    try:
        doreraise = plugin._dont_swallow_my_exceptions
    except AttributeError:
        return
    if doreraise:
        raise


MultiPlugins = []


def registerMultiPlugin(meta_type):
    """ Register a 'multi-plugin' in order to expose it to the Add List
    """
    if meta_type in MultiPlugins:
        raise RuntimeError('Meta-type (%s) already available to Add List'
                           % meta_type)
    MultiPlugins.append(meta_type)


class DumbHTTPExtractor(Implicit):

    security = ClassSecurityInfo()

    @security.private
    def extractCredentials(self, request):
        """ Pull HTTP credentials out of the request.
        """
        creds = {}
        login_pw = request._authUserPW()

        if login_pw is not None:
            name, password = login_pw

            creds['login'] = name
            creds['password'] = password
            creds['remote_host'] = request.get('REMOTE_HOST', '')

            try:
                creds['remote_address'] = request.getClientAddr()
            except AttributeError:
                creds['remote_address'] = request.get('REMOTE_ADDR', '')

        return creds


classImplements(DumbHTTPExtractor, ILoginPasswordHostExtractionPlugin)


InitializeClass(DumbHTTPExtractor)


class EmergencyUserAuthenticator(Implicit):

    security = ClassSecurityInfo()

    @security.private
    def authenticateCredentials(self, credentials):
        """ Check credentials against the emergency user.
        """
        if isinstance(credentials, dict):

            eu = emergency_user
            eu_name = eu.getUserName()
            login = credentials.get('login')

            if login == eu_name:
                password = credentials.get('password')

                if eu.authenticate(password, {}):
                    return (eu_name, None)

        return (None, None)


classImplements(EmergencyUserAuthenticator, IAuthenticationPlugin)


InitializeClass(EmergencyUserAuthenticator)


class PluggableAuthService(Folder, Cacheable):

    """ All-singing, all-dancing user folder.
    """
    security = ClassSecurityInfo()

    meta_type = 'Pluggable Auth Service'
    zmi_icon = 'fa fa-users-cog'
    zmi_show_add_dialog = False

    _id = id = 'acl_users'

    _emergency_user = emergency_user
    _nobody = nobody

    maxlistusers = -1   # Don't allow local role form to try to list us!

    # Method for transforming a login name.  This needs to be the name
    # of a method on this plugin.  See the applyTransform method.
    login_transform = ''

    _properties = (
        dict(id='title', type='string', mode='w', label='Title'),
        dict(id='login_transform', type='string', mode='w',
             label='Transform to apply to login name'),
    )

    def getId(self):

        return self._id

    #
    #   IUserFolder implementation
    #
    @security.protected(ManageUsers)
    def getUser(self, name):
        """ See IUserFolder.
        """
        plugins = self._getOb('plugins')

        name = self.applyTransform(name)
        user_info = self._verifyUser(plugins, login=name)

        if not user_info:
            return None

        return self._findUser(plugins, user_info['id'], user_info['login'])

    @security.protected(ManageUsers)
    def getUserById(self, id, default=None):
        """ See IUserFolder.
        """
        plugins = self._getOb('plugins')

        user_info = self._verifyUser(plugins, user_id=id)

        if not user_info:
            return default

        return self._findUser(plugins, user_info['id'], user_info['login'])

    @security.public
    def validate(self, request, auth='', roles=_noroles):
        """ See IUserFolder.
        """
        plugins = self._getOb('plugins')
        is_top = self._isTop()

        if not is_top and self._isNotCompetent(request, plugins):
            # this user folder should not try to authenticate this request
            return None

        user_ids = self._extractUserIds(request, plugins)
        (accessed, container, name, value) = \
            self._getObjectContext(request['PUBLISHED'], request)

        for user_id, login in user_ids:

            user = self._findUser(plugins, user_id, login, request=request)

            if aq_base(user) is emergency_user:

                if is_top:
                    return user
                else:
                    return None

            if self._authorizeUser(user, accessed, container, name, value,
                                   roles):
                return user

        if not is_top:
            return None

        #
        #   No other user folder above us can satisfy, and we have no user;
        #   return a constructed anonymous only if anonymous is authorized.
        #
        anonymous = self._createAnonymousUser(plugins)
        if self._authorizeUser(anonymous, accessed, container, name,
                               value, roles):
            return anonymous

        return None

    @security.protected(SearchPrincipals)
    def searchUsers(self, **kw):
        """ Search for users
        """
        search_name = kw.get('name', None)

        result = []
        max_results = kw.get('max_results', '')
        sort_by = kw.get('sort_by', '')

        # We apply sorting and slicing here across all sets, so don't
        # make the plugin do it
        if sort_by:
            del kw['sort_by']
        if max_results:
            del kw['max_results']
        if search_name:
            if kw.get('id') is not None:
                del kw['id']  # don't even bother searching by id
            # Note: name can be a sequence.
            kw['login'] = self.applyTransform(kw['name'])
        if kw.get('login', None):
            kw['login'] = self.applyTransform(kw['login'])

        plugins = self._getOb('plugins')
        enumerators = plugins.listPlugins(IUserEnumerationPlugin)

        for enumerator_id, enum in enumerators:
            try:
                user_list = enum.enumerateUsers(**kw)
                for user_info in user_list:
                    info = {}
                    info.update(user_info)
                    info['userid'] = info['id']
                    info['principal_type'] = 'user'
                    if 'title' not in info:
                        info['title'] = info['login']
                    result.append(info)

            except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
                reraise(enum)
                logger.debug('UserEnumerationPlugin %s error' % enumerator_id,
                             exc_info=True)

        if sort_by:
            result = sorted(result, key=lambda x: x.get(sort_by, '').lower())

        if max_results:
            try:
                max_results = int(max_results)
                result = result[:max_results]
            except ValueError:
                pass

        return tuple(result)

    @security.protected(SearchPrincipals)
    def searchGroups(self, **kw):
        """ Search for groups
        """
        search_name = kw.get('name', None)

        result = []
        max_results = kw.get('max_results', '')
        sort_by = kw.get('sort_by', '')

        # We apply sorting and slicing here across all sets, so don't
        # make the plugin do it
        if sort_by:
            del kw['sort_by']
        if max_results:
            del kw['max_results']
        if search_name:
            if kw.get('id') is not None:
                del kw['id']
            if 'title' not in kw:
                kw['title'] = kw['name']

        plugins = self._getOb('plugins')
        enumerators = plugins.listPlugins(IGroupEnumerationPlugin)

        for enumerator_id, enum in enumerators:
            try:
                group_list = enum.enumerateGroups(**kw)
                for group_info in group_list:
                    info = {}
                    info.update(group_info)
                    info['groupid'] = info['id']
                    info['principal_type'] = 'group'
                    if 'title' not in info:
                        info['title'] = '(Group) %s' % info['groupid']
                    result.append(info)
            except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
                reraise(enum)
                logger.debug('GroupEnumerationPlugin %s error' % enumerator_id,
                             exc_info=True)

        if sort_by:
            result = sorted(result, key=lambda x: x.get(sort_by, '').lower())

        if max_results:
            try:
                max_results = int(max_results)
                result = result[:max_results + 1]
            except ValueError:
                pass

        return tuple(result)

    @security.protected(SearchPrincipals)
    def searchPrincipals(self, groups_first=False, **kw):
        """ Search for principals (users, groups, or both)
        """
        max_results = kw.get('max_results', '')

        search_name = kw.get('name', None)
        if search_name:
            if 'title' not in kw:
                kw['title'] = search_name
            kw['login'] = search_name

        # For groups we search the original name
        # (e.g. Administrators), for users we apply the transform,
        # which could lowercase the name.
        groups = [d.copy() for d in self.searchGroups(**kw)]
        if kw.get('login', None):
            kw['login'] = self.applyTransform(kw['login'])
        users = [d.copy() for d in self.searchUsers(**kw)]

        if groups_first:
            result = groups + users
        else:
            result = users + groups

        if max_results:
            try:
                max_results = int(max_results)
                result = result[:max_results + 1]
            except ValueError:
                pass

        return tuple(result)

    @security.private
    def __creatable_by_emergency_user__(self):
        return 1

    @security.private
    def _setObject(self, id, object, roles=None, user=None, set_owner=0,
                   suppress_events=False):
        #
        #   Override ObjectManager's version to change the default for
        #   'set_owner' (we don't want to enforce ownership on contained
        #   objects).
        Folder._setObject(self, id, object, roles, user, set_owner)

    @security.private
    def _delOb(self, id):
        #
        #   Override ObjectManager's version to clean up any plugin
        #   registrations for the deleted object
        #
        plugins = self._getOb('plugins', None)

        if plugins is not None:
            plugins.removePluginById(id)

        Folder._delOb(self, id)

    #
    # ZMI stuff
    #
    security.declareProtected(ManageUsers, 'manage_search')  # NOQA: D001
    manage_search = PageTemplateFile('www/pasSearch', globals())

    manage_options = (Folder.manage_options[:1]
                      + ({'label': 'Search', 'action': 'manage_search'},)
                      + Folder.manage_options[2:]
                      + Cacheable.manage_options)

    @security.protected(ManageUsers)
    def resultsBatch(self, results, REQUEST, size=20, orphan=2, overlap=0):
        """ ZMI helper for getting batching for displaying search results
        """
        try:
            start_val = REQUEST.get('batch_start', '0')
            start = int(start_val)
            size = int(REQUEST.get('batch_size', size))
        except ValueError:
            start = 0

        batch = Batch(results, size, start, 0, orphan, overlap)

        if batch.end < len(results):
            qs = self._getBatchLink(REQUEST.get('QUERY_STRING', ''),
                                    start, batch.end)
            REQUEST.set('next_batch_url', '%s?%s' % (REQUEST.get('URL'), qs))

        if start > 0:
            new_start = start - size - 1

            if new_start < 0:
                new_start = 0

            qs = self._getBatchLink(REQUEST.get('QUERY_STRING', ''),
                                    start, new_start)
            REQUEST.set('previous_batch_url',
                        '%s?%s' % (REQUEST.get('URL'), qs))

        return batch

    @security.private
    def _getBatchLink(self, qs, old_start, new_start):
        """ Internal helper to generate correct query strings
        """
        if new_start is not None:
            if not qs:
                qs = 'batch_start=%d' % new_start
            elif qs.startswith('batch_start='):
                qs = qs.replace('batch_start=%d' % old_start,
                                'batch_start=%d' % new_start)
            elif qs.find('&batch_start=') != -1:
                qs = qs.replace('&batch_start=%d' % old_start,
                                '&batch_start=%d' % new_start)
            else:
                qs = '%s&batch_start=%d' % (qs, new_start)

        return qs

    #
    #   Helper methods
    #
    @security.private
    def _isNotCompetent(self, request, plugins):
        """ return true when this user folder should not try authentication.

        Never called for top level user folder.
        """
        try:
            not_competents = plugins.listPlugins(INotCompetentPlugin)
        except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
            logger.debug('NotCompetent plugin listing error', exc_info=True)
            not_competents = ()

        for not_competent_id, not_competent in not_competents:
            try:
                if not_competent.isNotCompetentToAuthenticate(request):
                    return True
            except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
                reraise(not_competent)
                logger.debug('NotCompetentPlugin %s error' % not_competent_id,
                             exc_info=True)
                continue
        return False

    @security.private
    def _extractUserIds(self, request, plugins):
        """ request -> [(validated_user_id, login)]

        o For each set of extracted credentials, try to authenticate
          a user;  accumulate a list of pairs (ID, login) of such users
          over all our authentication and extraction plugins.
        """
        try:
            extractors = plugins.listPlugins(IExtractionPlugin)
        except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
            logger.debug('Extractor plugin listing error', exc_info=True)
            extractors = ()

        if not extractors:
            extractors = (('default', DumbHTTPExtractor()),)

        try:
            authenticators = plugins.listPlugins(IAuthenticationPlugin)
        except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
            logger.debug('Authenticator plugin listing error', exc_info=True)
            authenticators = ()

        result = []

        for extractor_id, extractor in extractors:

            try:
                credentials = extractor.extractCredentials(request)
            except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
                reraise(extractor)
                logger.debug('ExtractionPlugin %s error' % extractor_id,
                             exc_info=True)
                continue

            if credentials:

                try:
                    credentials['extractor'] = extractor_id  # ??? in key?
                    # Test if ObjectCacheEntries.aggregateIndex would work
                    items = sorted(credentials.items())  # noqa
                except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
                    # ???: would reraise be good here, and which plugin to ask
                    # whether not to swallow the exception - the extractor?
                    logger.debug('Credentials error: %s' % credentials,
                                 exc_info=True)
                    continue

                # First try to authenticate against the emergency
                # user and return immediately if authenticated
                user_id, name = self._tryEmergencyUserAuthentication(
                    credentials)

                if user_id is not None:
                    return [(user_id, name)]

                # Now see if the user ids can be retrieved from the cache
                credentials['login'] = self.applyTransform(
                    credentials.get('login'))
                view_name = createViewName('_extractUserIds',
                                           credentials.get('login'))
                keywords = createKeywords(**credentials)
                user_ids = self.ZCacheable_get(view_name=view_name,
                                               keywords=keywords,
                                               default=None)
                if user_ids is None:
                    user_ids = []

                    for authenticator_id, auth in authenticators:

                        try:
                            uid_and_info = auth.authenticateCredentials(
                                credentials)

                            if uid_and_info is None:
                                continue

                            user_id, info = uid_and_info

                        except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
                            reraise(auth)
                            msg = 'AuthenticationPlugin %s error' % (
                                authenticator_id,)
                            logger.debug(msg, exc_info=True)
                            continue

                        if user_id is not None:
                            user_ids.append((user_id, info))

                    if user_ids:
                        self.ZCacheable_set(user_ids, view_name=view_name,
                                            keywords=keywords)

                result.extend(user_ids)

        # Emergency user via HTTP basic auth always wins
        user_id, name = self._tryEmergencyUserAuthentication(
            DumbHTTPExtractor().extractCredentials(request))

        if user_id is not None:
            return [(user_id, name)]

        return result

    @security.private
    def _tryEmergencyUserAuthentication(self, credentials):
        """ credentials -> emergency_user or None
        """
        try:
            eua = EmergencyUserAuthenticator()
            user_id, name = eua.authenticateCredentials(credentials)
        except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
            logger.debug('Credentials error: %s' % credentials, exc_info=True)
            user_id, name = (None, None)

        return (user_id, name)

    @security.private
    def _getGroupsForPrincipal(self, principal, request=None, plugins=None,
                               ignore_plugins=None):
        all_groups = {}

        if ignore_plugins is None:
            ignore_plugins = ()

        if plugins is None:
            plugins = self._getOb('plugins')
        groupmakers = plugins.listPlugins(IGroupsPlugin)

        for groupmaker_id, groupmaker in groupmakers:

            if groupmaker_id in ignore_plugins:
                continue
            groups = groupmaker.getGroupsForPrincipal(principal, request)
            for group in groups:
                principal._addGroups([group])
                all_groups[group] = 1

        return all_groups.keys()

    @security.private
    def _createAnonymousUser(self, plugins):
        """ Allow IAnonymousUserFactoryPlugins to create or fall back.
        """
        factories = plugins.listPlugins(IAnonymousUserFactoryPlugin)

        for factory_id, factory in factories:

            anon = factory.createAnonymousUser()

            if anon is not None:
                return anon.__of__(self)

        return nobody.__of__(self)

    @security.private
    def _createUser(self, plugins, user_id, name):
        """ Allow IUserFactoryPlugins to create, or fall back to default.
        """
        name = self.applyTransform(name)
        factories = plugins.listPlugins(IUserFactoryPlugin)

        for factory_id, factory in factories:

            user = factory.createUser(user_id, name)

            if user is not None:
                return user.__of__(self)

        return PropertiedUser(user_id, name).__of__(self)

    @security.private
    def _findUser(self, plugins, user_id, name=None, request=None):
        """ user_id -> decorated_user
        """
        if user_id == self._emergency_user.getUserName():
            return self._emergency_user

        # See if the user can be retrieved from the cache
        view_name = createViewName('_findUser', user_id)
        name = self.applyTransform(name)
        keywords = createKeywords(user_id=user_id, name=name)
        user = self.ZCacheable_get(view_name=view_name, keywords=keywords,
                                   default=None)

        if user is None:

            user = self._createUser(plugins, user_id, name)
            propfinders = plugins.listPlugins(IPropertiesPlugin)

            for propfinder_id, propfinder in propfinders:

                data = propfinder.getPropertiesForUser(user, request)
                if data:
                    user.addPropertysheet(propfinder_id, data)

            groups = self._getGroupsForPrincipal(user, request,
                                                 plugins=plugins)
            user._addGroups(groups)

            rolemakers = plugins.listPlugins(IRolesPlugin)

            for rolemaker_id, rolemaker in rolemakers:
                try:
                    roles = rolemaker.getRolesForPrincipal(user, request)
                except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
                    logger.debug('IRolesPlugin %s error' % rolemaker_id,
                                 exc_info=True)
                else:
                    if roles:
                        user._addRoles(roles)

            user._addRoles(['Authenticated'])

            # Cache the user if caching is enabled
            base_user = aq_base(user)
            if getattr(base_user, '_p_jar', None) is None:
                self.ZCacheable_set(base_user, view_name=view_name,
                                    keywords=keywords)

        return user.__of__(self)

    @security.private
    def _verifyUser(self, plugins, user_id=None, login=None):
        """ user_id -> info_dict or None
        """
        if user_id is None and login is None:
            # Avoid possible hugely expensive and/or wrong behavior of
            # plugin enumerators.
            return None

        criteria = {'exact_match': True}

        if user_id is not None:
            criteria['id'] = user_id

        if login is not None:
            criteria['login'] = self.applyTransform(login)

        view_name = createViewName('_verifyUser', user_id or login)
        keywords = createKeywords(**criteria)
        cached_info = self.ZCacheable_get(view_name=view_name,
                                          keywords=keywords, default=None)

        if cached_info is not None:
            return cached_info

        enumerators = plugins.listPlugins(IUserEnumerationPlugin)

        for enumerator_id, enumerator in enumerators:
            try:
                info = enumerator.enumerateUsers(**criteria)

                if info:
                    # Put the computed value into the cache
                    self.ZCacheable_set(info[0], view_name=view_name,
                                        keywords=keywords)
                    return info[0]

            except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
                reraise(enumerator)
                msg = 'UserEnumerationPlugin %s error' % enumerator_id
                logger.debug(msg, exc_info=True)

        return None

    @security.private
    def _authorizeUser(self, user, accessed, container, name, value,
                       roles=_noroles):
        """ -> boolean (whether user has roles).

        o Add the user to the SM's stack, if successful.

        o Return
        """
        user = aq_base(user).__of__(self)
        newSecurityManager(None, user)
        security = getSecurityManager()
        try:
            try:
                if roles is _noroles:
                    if security.validate(accessed, container, name, value):
                        return 1
                else:
                    if security.validate(accessed, container, name, value,
                                         roles):
                        return 1
            except:  # noqa
                noSecurityManager()
                raise

        except Unauthorized:
            pass

        return 0

    @security.private
    def _isTop(self):
        """ Are we the user folder in the root object?
        """
        try:
            parent = aq_base(aq_parent(self))
            if parent is None:
                return 0
            return parent.isTopLevelPrincipiaApplicationObject
        except AttributeError:
            return 0

    @security.private
    def _getObjectContext(self, v, request):
        """ request -> (a, c, n, v)

        o 'a 'is the object the object was accessed through

        o 'c 'is the physical container of the object

        o 'n 'is the name used to access the object

        o 'v' is the object (value) we're validating access to

        o ???:  Lifted from AccessControl.User.BasicUserFolder._getobcontext
        """
        if len(request.steps) == 0:  # someone deleted root index_html

            request['RESPONSE'].notFoundError(
                'no default view (root default view was probably deleted)')

        root = request['PARENTS'][-1]
        request_container = aq_parent(root)

        n = request.steps[-1]

        # default to accessed and container as v.aq_parent
        a = c = request['PARENTS'][0]

        # try to find actual container
        inner = aq_inner(v)
        innerparent = aq_parent(inner)

        if innerparent is not None:

            # this is not a method, we needn't treat it specially
            c = innerparent

        elif hasattr(v, '__self__'):

            # this is a method, we need to treat it specially
            c = v.__self__
            c = aq_inner(v)

        # if pub's aq_parent or container is the request container, it
        # means pub was accessed from the root
        if a is request_container:
            a = root

        if c is request_container:
            c = root

        return a, c, n, v

    @security.private
    def _getEmergencyUser(self):

        return emergency_user.__of__(self)

    @security.private
    def _doAddUser(self, login, password, roles, domains, **kw):
        """ Create a user with login, password and roles if, and only if,
            we have a registered user manager and role manager that will
            accept specific plugin interfaces.
        """
        plugins = self._getOb('plugins')
        useradders = plugins.listPlugins(IUserAdderPlugin)
        roleassigners = plugins.listPlugins(IRoleAssignerPlugin)

        user = None
        login = self.applyTransform(login)

        if not (useradders and roleassigners):
            raise NotImplementedError('There are no plugins'
                                      ' that can create'
                                      ' users and assign roles to them.')

        for useradder_id, useradder in useradders:
            if useradder.doAddUser(login, password):
                # ???: Adds user to cache, but without roles...
                user = self.getUser(login)
                break

        # No useradder was successful.
        if user is None:
            return

        for roleassigner_id, roleassigner in roleassigners:
            for role in roles:
                try:
                    roleassigner.doAssignRoleToPrincipal(user.getId(), role)
                except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
                    reraise(roleassigner)
                    logger.debug('RoleAssigner %s error' % roleassigner_id,
                                 exc_info=True)
                    pass

        if user is not None:
            notify(PrincipalCreated(user))
        return user

    @security.public
    def all_meta_types(self):
        """ What objects can be put in here?
        """
        import Products
        meta_types = Products.meta_types
        allowed_types = tuple(MultiPlugins) + (RAMCacheManager.meta_type,)

        meta_types = [x for x in meta_types if x['name'] in allowed_types]
        dlg_type = 'zmi_show_add_dialog'

        for mt in meta_types:
            want_modal = getattr(mt.get('instance', None), dlg_type, True)
            mt[dlg_type] = 'modal' if want_modal else ''

        return meta_types

    @security.private
    def manage_beforeDelete(self, item, container):
        if item is self:
            try:
                del container.__allow_groups__
            except:  # noqa
                pass

            handle = self.meta_type + '/' + self.getId()
            BeforeTraverse.unregisterBeforeTraverse(container, handle)

    @security.private
    def manage_afterAdd(self, item, container):
        if item is self:
            container.__allow_groups__ = aq_base(self)

            handle = self.meta_type + '/' + self.getId()
            container = container.this()
            nc = BeforeTraverse.NameCaller(self.getId())
            BeforeTraverse.registerBeforeTraverse(container, nc, handle)

    def __call__(self, container, req):
        """ The __before_publishing_traverse__ hook.
        """
        resp = req['RESPONSE']
        req._hold(ResponseCleanup(resp))
        stack = getattr(resp, '_unauthorized_stack', [])
        stack.append(resp._unauthorized)
        resp._unauthorized_stack = stack
        resp._unauthorized = self._unauthorized
        resp._has_challenged = False

    @security.private
    def applyTransform(self, value):
        """ Transform for login name.

        Possibly transform the login, for example by making it lower
        case.

        value must be a string (or unicode) or it may be a sequence
        (list, tuple), in which case we need to iterate over it.
        """
        if not value:
            return value
        transform = self._get_login_transform_method()
        if not transform:
            return value
        if isinstance(value, six.string_types):
            return transform(value)
        result = []
        for v in value:
            result.append(transform(v))
        if isinstance(value, tuple):
            return tuple(result)
        return result

    @security.private
    def _get_login_transform_method(self):
        """ Get the transform method for the login name or None.
        """
        login_transform = getattr(self, 'login_transform', None)
        if not login_transform:
            return
        transform = getattr(self, login_transform.strip(), None)
        if transform is None:
            logger.debug('Transform method %r not found in plugin %r.',
                         self.login_transform, self)
            return
        return transform

    @security.private
    def _setPropValue(self, id, value):
        if id == 'login_transform':
            orig_value = getattr(self, id)
        super(PluggableAuthService, self)._setPropValue(id, value)
        if id == 'login_transform' and value and value != orig_value:
            logger.debug('login_transform changed from %r to %r. '
                         'Updating existing login names.', orig_value, value)
            self.updateAllLoginNames()

    @security.private
    def lower(self, value):
        """ Transform for login name.

        Strip the value and lowercase it.

        To use this, set login_tranform to 'lower'.
        """
        return value.strip().lower()

    @security.private
    def upper(self, value):
        """ Transform for login name.

        Strip the value and uppercase it.

        To use this, set login_tranform to 'upper'.
        """
        return value.strip().upper()

    #
    # Response override
    #
    def _unauthorized(self):
        req = self.REQUEST
        resp = req['RESPONSE']
        if resp._has_challenged:  # Been here already
            return
        if not self.challenge(req, resp):
            # Need to fall back here
            resp = self._cleanupResponse()
            resp._unauthorized()
        else:
            resp._has_challenged = True

    def challenge(self, request, response):
        plugins = self._getOb('plugins')

        # Find valid protocols for this request type
        valid_protocols = []
        choosers = []
        try:
            choosers = plugins.listPlugins(IChallengeProtocolChooser)
        except KeyError:
            # Work around the fact that old instances might not have
            # IChallengeProtocolChooser registered with the
            # PluginRegistry.
            pass

        for chooser_id, chooser in choosers:
            choosen = chooser.chooseProtocols(request)
            if choosen is None:
                continue
            valid_protocols.extend(choosen)

        # Go through all challenge plugins
        challengers = plugins.listPlugins(IChallengePlugin)

        protocol = None

        for challenger_id, challenger in challengers:
            challenger_protocol = getattr(challenger, 'protocol',
                                          challenger_id)
            if valid_protocols and challenger_protocol not in valid_protocols:
                # Skip invalid protocol for this request type.
                continue
            if protocol is None or protocol == challenger_protocol:
                if challenger.challenge(request, response):
                    protocol = challenger_protocol

        if protocol is not None:
            # something fired, so it was a successful PAS challenge
            return True

        # nothing fired, so trigger the fallback
        return False

    def _cleanupResponse(self):
        resp = self.REQUEST['RESPONSE']
        # No errors of any sort may propagate, and we don't care *what*
        # they are, even to log them.
        stack = getattr(resp, '_unauthorized_stack', [])

        if stack:
            resp._unauthorized = stack.pop()
        else:
            try:
                del resp._unauthorized
            except:  # noqa
                pass

        return resp

    @security.public
    def hasUsers(self):
        """Zope quick start sacrifice.

        The quick start page expects a hasUsers() method.
        """
        return True

    @security.public
    def updateCredentials(self, request, response, login, new_password):
        """Central updateCredentials method

        This method is needed for cases where the credentials storage and
        the credentials extraction is handled by different plugins. Example
        case would be if the CookieAuthHelper is used as a Challenge and
        Extraction plugin only to take advantage of the login page feature
        but the credentials are not stored in the CookieAuthHelper cookie
        but somewhere else, like in a Session.
        """
        login = self.applyTransform(login)
        plugins = self._getOb('plugins')
        cred_updaters = plugins.listPlugins(ICredentialsUpdatePlugin)

        for updater_id, updater in cred_updaters:
            updater.updateCredentials(request, response, login, new_password)

    @security.public
    def logout(self, REQUEST):
        """Publicly accessible method to log out a user
        """
        self.resetCredentials(REQUEST, REQUEST['RESPONSE'])

        # Little bit of a hack: Issuing a redirect to the same place
        # where the user was so that in the second request the now-destroyed
        # credentials can be acted upon to e.g. go back to the login page
        referrer = REQUEST.get('HTTP_REFERER')  # optional header
        if referrer:
            REQUEST['RESPONSE'].redirect(url_local(referrer))

    @security.public
    def resetCredentials(self, request, response):
        """Reset credentials by informing all active resetCredentials plugins
        """
        user = getSecurityManager().getUser()
        if aq_base(user) is not nobody:
            plugins = self._getOb('plugins')
            cred_resetters = plugins.listPlugins(ICredentialsResetPlugin)

            for resetter_id, resetter in cred_resetters:
                resetter.resetCredentials(request, response)

    @security.protected(ManageUsers)
    def updateLoginName(self, user_id, login_name):
        """Update login name of user.
        """
        logger.debug('Called updateLoginName, user_id=%r, login_name=%r',
                     user_id, login_name)
        login_name = self.applyTransform(login_name)
        # Note: we do not call self.getUserById(user_id) here to see
        # if this user exists, or call getUserName() on the answer to
        # compare it with the transformed login name, because the user
        # may be reported with a login name that is transformed on the
        # fly, for example in the _verifyUser call, even though the
        # plugin has not actually transformed the login name yet in
        # the backend.
        self._updateLoginName(user_id, login_name)

    @security.public
    def updateOwnLoginName(self, login_name):
        """Update own login name of authenticated user.
        """
        logger.debug('Called updateOwnLoginName, login_name=%r', login_name)
        login_name = self.applyTransform(login_name)
        user = getSecurityManager().getUser()
        if aq_base(user) is nobody:
            return
        user_id = user.getId()
        # Note: we do not compare the login name here.  See the
        # comment in updateLoginName above.
        self._updateLoginName(user_id, login_name)

    def _updateLoginName(self, user_id, login_name):
        # Note: we do not compare the login name here.  See the
        # comment in updateLoginName above.
        plugins = self._getOb('plugins')
        updaters = plugins.listPlugins(IUserEnumerationPlugin)

        # Call the updaters.  One of them *must* succeed without an
        # exception, even if it does not change anything.  When a
        # login name is already taken, we do not want to fail
        # silently.
        success = False
        for updater_id, updater in updaters:
            if not hasattr(updater, 'updateUser'):
                # This was a later addition to the interface, so we
                # are forgiving.
                logger.warn('%s plugin lacks updateUser method of '
                            'IUserEnumerationPlugin.', updater_id)
                continue
            try:
                result = updater.updateUser(user_id, login_name)
            except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
                reraise(updater)
                logger.debug('UpdateLoginNamePlugin %s error' % updater_id,
                             exc_info=True)
            else:
                if result:
                    success = True
                    logger.debug('login name changed to: %r', login_name)

        if not success:
            raise ValueError('Cannot update login name of user %r to %r. '
                             'Possibly duplicate.' % (user_id, login_name))

    @security.protected(ManageUsers)
    def updateAllLoginNames(self, quit_on_first_error=True):
        """Update login names of all users to their canonical value.

        This should be done after changing the login_transform
        property of PAS.

        You can set quit_on_first_error to False to report all errors
        before quitting with an error.  This can be useful if you want
        to know how many problems there are, if any.
        """
        plugins = self._getOb('plugins')
        updaters = plugins.listPlugins(IUserEnumerationPlugin)
        for updater_id, updater in updaters:
            if not hasattr(updater, 'updateEveryLoginName'):
                # This was a later addition to the interface, so we
                # are forgiving.
                logger.warn('%s plugin lacks updateEveryLoginName method of '
                            'IUserEnumerationPlugin.', updater_id)
                continue
            # Note: do not swallow any exceptions here.
            updater.updateEveryLoginName(
                quit_on_first_error=quit_on_first_error)


classImplements(PluggableAuthService,
                (IPluggableAuthService, IObjectManager, IPropertyManager))


InitializeClass(PluggableAuthService)


class ResponseCleanup:
    def __init__(self, resp):
        self.resp = resp

    def __del__(self):
        # Free the references.
        #
        # No errors of any sort may propagate, and we don't care *what*
        # they are, even to log them.
        stack = getattr(self.resp, '_unauthorized_stack', [])
        old = None

        while stack:
            old = stack.pop()

        if old is not None:
            self.resp._unauthorized = old
        else:
            try:
                del self.resp._unauthorized
            except:  # noqa
                pass

        try:
            del self.resp
        except:  # noqa
            pass


_PLUGIN_TYPE_INFO = (
    (IExtractionPlugin, 'IExtractionPlugin', 'extraction',
     'Extraction plugins are responsible for extracting credentials '
     'from the request.'),
    (IAuthenticationPlugin, 'IAuthenticationPlugin', 'authentication',
     'Authentication plugins are responsible for validating credentials '
     'generated by the Extraction Plugin.'),
    (IChallengePlugin, 'IChallengePlugin', 'challenge',
     'Challenge plugins initiate a challenge to the user to provide '
     'credentials.'),
    (ICredentialsUpdatePlugin, 'ICredentialsUpdatePlugin',
     'update credentials',
     'Credential update plugins respond to the user changing '
     'credentials.'),
    (ICredentialsResetPlugin, 'ICredentialsResetPlugin', 'reset credentials',
     'Credential clear plugins respond to a user logging out.'),
    (IUserFactoryPlugin, 'IUserFactoryPlugin', 'userfactory', 'Create users.'),
    (IAnonymousUserFactoryPlugin, 'IAnonymousUserFactoryPlugin',
     'anonymoususerfactory', 'Create anonymous users.'),
    (IPropertiesPlugin, 'IPropertiesPlugin', 'properties',
     'Properties plugins generate property sheets for users.'),
    (IGroupsPlugin, 'IGroupsPlugin', 'groups',
     'Groups plugins determine the groups to which a user belongs.'),
    (IRolesPlugin, 'IRolesPlugin', 'roles',
     'Roles plugins determine the global roles which a user has.'),
    (IUpdatePlugin, 'IUpdatePlugin', 'update',
     'Update plugins allow the user or the application to update '
     "the user's properties."),  # noqa: Q000
    (IValidationPlugin, 'IValidationPlugin', 'validation',
     'Validation plugins specify allowable values for user properties '
     '(e.g., minimum password length, allowed characters, etc.)'),
    (IUserEnumerationPlugin, 'IUserEnumerationPlugin', 'user_enumeration',
     'Enumeration plugins allow querying users by ID, and searching for '
     'users who match particular criteria.'),
    (IUserAdderPlugin, 'IUserAdderPlugin', 'user_adder',
     'User Adder plugins allow the Pluggable Auth Service to create users.'),
    (IGroupEnumerationPlugin, 'IGroupEnumerationPlugin', 'group_enumeration',
     'Enumeration plugins allow querying groups by ID.'),
    (IRoleEnumerationPlugin, 'IRoleEnumerationPlugin', 'role_enumeration',
     'Enumeration plugins allow querying roles by ID.'),
    (IRoleAssignerPlugin, 'IRoleAssignerPlugin', 'role_assigner',
     'Role Assigner plugins allow the Pluggable Auth Service to assign'
     ' roles to principals.'),
    (IChallengeProtocolChooser, 'IChallengeProtocolChooser',
     'challenge_protocol_chooser',
     'Challenge Protocol Chooser plugins decide what authorization'
     'protocol to use for a given request type.'),
    (IRequestTypeSniffer, 'IRequestTypeSniffer', 'request_type_sniffer',
     'Request Type Sniffer plugins detect the type of an incoming request.'),
    (INotCompetentPlugin, 'INotCompetentPlugin', 'notcompetent',
     'Not-Competent plugins check whether this user folder should not '
     'authenticate the current request. '
     'These plugins are not used for a top level user folder. '
     'They are typically used to prevent shadowing of authentications by '
     'higher level user folders.'))


def addPluggableAuthService(dispatcher, base_profile=None,
                            extension_profiles=(), create_snapshot=True,
                            setup_tool_id='setup_tool', REQUEST=None):
    """ Add a PluggableAuthService to 'dispatcher'.

    o BBB for non-GenericSetup use.
    """
    pas = PluggableAuthService()
    preg = PluginRegistry(_PLUGIN_TYPE_INFO)
    preg._setId('plugins')
    pas._setObject('plugins', preg)
    dispatcher._setObject(pas.getId(), pas)

    if REQUEST is not None:
        REQUEST['RESPONSE'].redirect('%s/manage_workspace'
                                     '?manage_tabs_message='
                                     'PluggableAuthService+added.' %
                                     dispatcher.absolute_url())


def addConfiguredPASForm(dispatcher):
    """ Wrap the PTF in 'dispatcher', including 'profile_registry' in options.
    """
    from Products.GenericSetup import EXTENSION
    from Products.GenericSetup import profile_registry

    wrapped = PageTemplateFile('pasAddForm', _wwwdir).__of__(dispatcher)

    base_profiles = []
    extension_profiles = []

    for info in profile_registry.listProfileInfo(for_=IPluggableAuthService):
        if info.get('type') == EXTENSION:
            extension_profiles.append(info)
        else:
            base_profiles.append(info)

    return wrapped(base_profiles=tuple(base_profiles),
                   extension_profiles=tuple(extension_profiles))


def addConfiguredPAS(dispatcher, base_profile, extension_profiles=(),
                     create_snapshot=True, setup_tool_id='setup_tool',
                     REQUEST=None):
    """ Add a PluggableAuthService to 'self.
    """
    from Products.GenericSetup.tool import SetupTool

    pas = PluggableAuthService()
    preg = PluginRegistry(_PLUGIN_TYPE_INFO)
    preg._setId('plugins')
    pas._setObject('plugins', preg)
    dispatcher._setObject(pas.getId(), pas)

    pas = dispatcher._getOb(pas.getId())    # wrapped
    tool = SetupTool(setup_tool_id)
    pas._setObject(tool.getId(), tool)

    tool = pas._getOb(tool.getId())       # wrapped
    tool.runAllImportStepsFromProfile('profile-%s' % base_profile)

    for extension_profile in extension_profiles:
        tool.runAllImportStepsFromProfile('profile-%s' % extension_profile)

    if create_snapshot:
        tool.createSnapshot('initial_configuration')

    if REQUEST is not None:
        REQUEST['RESPONSE'].redirect('%s/manage_workspace'
                                     '?manage_tabs_message='
                                     'PluggableAuthService+added.' %
                                     dispatcher.absolute_url())
