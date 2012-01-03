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
""" DomainAuthHelper   Authentication Plugin for Domain authentication
"""

__doc__     = """ Authentication Plugin for Domain authentication """
__version__ = '$Revision$'[11:-2]

# General Python imports
import socket
import os
import time
import copy
import re

try:
    from IPy import IP
except ImportError:
    IP = None

# General Zope imports
from BTrees.OOBTree import OOBTree
from App.class_init import InitializeClass
from AccessControl import ClassSecurityInfo
from AccessControl.Permissions import manage_users

from zope.interface import Interface

from Products.PageTemplates.PageTemplateFile import PageTemplateFile

# PluggableAuthService imports
from Products.PluggableAuthService.interfaces.plugins import \
    IAuthenticationPlugin
from Products.PluggableAuthService.interfaces.plugins import \
    IExtractionPlugin
from Products.PluggableAuthService.interfaces.plugins import \
    IRolesPlugin
from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin
from Products.PluggableAuthService.utils import classImplements

class IDomainAuthHelper(Interface):
    """ Marker interface.
    """

class EqualsFilter:

    def __init__(self, matchstring):
        self.match_string = matchstring

    def __call__(self, candidate):
        return candidate == self.match_string

class StartsWithFilter:

    def __init__(self, matchstring):
        self.match_string = matchstring

    def __call__(self, candidate):
        return candidate.startswith(self.match_string)

class EndsWithFilter:

    def __init__(self, matchstring):
        self.match_string = matchstring

    def __call__(self, candidate):
        return candidate.endswith(self.match_string)

class RegexFilter:

    def __init__(self, matchstring):
        self.regex = re.compile(matchstring)

    def __call__(self, candidate):
        return self.regex.match(candidate)

_MATCH_TYPE_FILTERS = {
    'equals': EqualsFilter,
    'startswith': StartsWithFilter,
    'endswith': EndsWithFilter,
    'regex': RegexFilter,
}

if IP is not None:
    class IPFilter:

        def __init__(self, matchstring):
            self.ip = IP(matchstring)

        def __call__(self, candidate):
            try:
                c_ip = IP(candidate)
            except ValueError:
                return False
            return c_ip in self.ip

    _MATCH_TYPE_FILTERS['ip'] = IPFilter

manage_addDomainAuthHelperForm = PageTemplateFile(
    'www/daAdd', globals(), __name__='manage_addDomainAuthHelperForm' )

def manage_addDomainAuthHelper(self, id, title='', REQUEST=None):
    """ Factory method to instantiate a DomainAuthHelper """
    obj = DomainAuthHelper(id, title=title)
    self._setObject(id, obj)

    if REQUEST is not None:
        qs = 'manage_tabs_message=DomainAuthHelper+added.'
        my_url = self.absolute_url()
        REQUEST['RESPONSE'].redirect('%s/manage_workspace?%s' % (my_url, qs))


class DomainAuthHelper(BasePlugin):
    """ Domain Authentication plugin for the PluggableAuthService """
    security = ClassSecurityInfo()
    meta_type = 'Domain Authentication Plugin'

    security.declareProtected(manage_users, 'manage_map')
    manage_map = PageTemplateFile('www/daMatches', globals())

    security.declareProtected(manage_users, 'manage_genericmap')
    manage_genericmap = PageTemplateFile('www/daGeneric', globals())

    manage_options = ( BasePlugin.manage_options[:1]
                     + ( { 'label'  : 'User Map'
                         , 'action' : 'manage_map'
                       # , 'help'   : ( 'PluggableAuthService'
                       #              ,'matches.stx')
                         }
                       , { 'label'  : 'Generic Map'
                         , 'action' : 'manage_genericmap'
                         }
                       )
                     + BasePlugin.manage_options[1:]
                     )


    def __init__(self, id, title=''):
        """ Initialize a new instance """
        self.id = id
        self.title = title
        self._domain_map = OOBTree()


    security.declarePrivate('extractCredentials')
    def extractCredentials(self, request):
        """ Extract credentials from 'request'.
        """
        creds = {}

        remote_host = request.get('REMOTE_HOST', '')
        if remote_host:
            creds['remote_host'] = request.get('REMOTE_HOST', '')

        try:
            remote_address = request.getClientAddr()
        except AttributeError:
            remote_address = request.get('REMOTE_ADDR', '')

        if remote_host or remote_address:
            creds['remote_host'] = remote_host
            creds['remote_address'] = remote_address

        return creds

    security.declarePrivate('authenticateCredentials')
    def authenticateCredentials(self, credentials):
        """ Fulfill AuthenticationPlugin requirements """
        login = credentials.get('login', '')
        r_host = credentials.get('remote_host', '')
        r_address = credentials.get('remote_address', '')
        matches = self._findMatches(login, r_host, r_address)

        if len(matches) > 0:
            if login:
                return (login, login)
            else:
                best_match = matches[0]
                u_name = best_match.get('username', 'remote')
                return ( best_match.get('user_id', u_name)
                       , u_name
                       )

        return (None, None)


    security.declarePrivate( 'getRolesForPrincipal' )
    def getRolesForPrincipal(self, user, request=None):
        """ Fulfill RolesPlugin requirements """
        roles = []

        if request is None:
            # Without request there is no way I can do anything...
            return tuple(roles)

        uname = user.getUserName()

        if uname.find('Remote User') != -1:
            uname = ''

        matches = self._findMatches( uname
                                   , request.get('REMOTE_HOST', '')
                                   , request.getClientAddr()
                                   )

        # We want to grab the first match because it is the most specific
        if len(matches) > 0:
            roles = matches[0].get('roles', [])

        return tuple(roles)


    security.declarePrivate('_findMatches')
    def _findMatches(self, login, r_host='', r_address=''):
        """ Find the match """
        matches = []

        if not r_host and not r_address:
            return tuple(matches)

        all_info = list(self._domain_map.get(login, []))
        all_info.extend(self._domain_map.get('', []))

        if not r_host:
            try:
                r_host = socket.gethostbyaddr(r_address)[0]
            except socket.error:
                pass

        if not r_address:
            try:
                r_address = socket.gethostbyname(r_host)
            except socket.error :
                pass

        if not r_host and not r_address:
            return tuple(matches)

        candidates = [r_host, r_address]

        for match_info in all_info:
            m = []
            m_type = match_info['match_type']
            m_string = match_info['match_string']
            filter = match_info.get('match_filter')

            if filter is None:  # legacy data
                filter = _MATCH_TYPE_FILTERS[m_type](m_string)

            matches.extend([match_info for x in candidates if filter(x)])

        return tuple(matches)


    security.declareProtected(manage_users, 'listMatchTypes')
    def listMatchTypes(self):
        """ Return a sequence of possible match types """
        return _MATCH_TYPE_FILTERS.keys()


    security.declareProtected(manage_users, 'listMappingsForUser')
    def listMappingsForUser(self, user_id=''):
        """ List the mappings for a specific user """
        result = []
        record = self._domain_map.get(user_id, [])

        for match_info in record:
            result.append( { 'match_type' : match_info['match_type']
                           , 'match_string' : match_info['match_string']
                           , 'match_id' : match_info['match_id']
                           , 'roles' : match_info['roles']
                           , 'username' : match_info['username']
                           } )

        return result


    security.declareProtected(manage_users, 'manage_addMapping')
    def manage_addMapping( self
                         , user_id=''
                         , match_type=''
                         , match_string=''
                         , username=''
                         , roles=[]
                         , REQUEST=None
                         ):
        """ Add a mapping for a user """
        msg = ''

        try:
            filter = _MATCH_TYPE_FILTERS[match_type](match_string)
        except KeyError:
            msg = 'Unknown match type %s' % match_type
        except re.error:
            msg = 'Invalid regular expression %s' % match_string
        except ValueError, e:
            msg = 'Invalid match string %s (%s)' % (match_string, e)

        if not match_string:
            msg = 'No match string specified'

        if msg:
            if REQUEST is not None:
                return self.manage_map(manage_tabs_message=msg)

            raise ValueError, msg

        record = self._domain_map.get(user_id, [])

        match = { 'match_type' : match_type
                , 'match_string' : match_string
                , 'match_filter' : filter
                , 'match_id' : '%s_%s' % (user_id, str(time.time()))
                , 'username' : user_id or username or 'Remote User'
                , 'roles' : roles
                }

        if match not in record:
            record.append(match)
        else:
            msg = 'Match already exists'

        self._domain_map[user_id] = record

        if REQUEST is not None:
            msg = msg or 'Match added.'
            if user_id:
                return self.manage_map(manage_tabs_message=msg)
            else:
                return self.manage_genericmap(manage_tabs_message=msg)


    security.declareProtected(manage_users, 'manage_removeMappings')
    def manage_removeMappings(self, user_id='', match_ids=[], REQUEST=None):
        """ Remove mappings """
        msg = ''

        if len(match_ids) < 1:
            msg = 'No matches specified'

        record = self._domain_map.get(user_id, [])

        if len(record) < 1:
            msg = 'No mappings for user %s' % user_id

        if msg:
            if REQUEST is not None:
                return self.manage_map(manage_tabs_message=msg)
            else:
                return

        to_delete = [x for x in record if x['match_id'] in match_ids]

        for match in to_delete:
            record.remove(match)

        self._domain_map[user_id] = record

        if REQUEST is not None:
            msg = 'Matches deleted'
            if user_id:
                return self.manage_map(manage_tabs_message=msg)
            else:
                return self.manage_genericmap(manage_tabs_message=msg)

classImplements( DomainAuthHelper
               , IDomainAuthHelper
               , IExtractionPlugin
               , IAuthenticationPlugin
               , IRolesPlugin
               )

InitializeClass(DomainAuthHelper)

