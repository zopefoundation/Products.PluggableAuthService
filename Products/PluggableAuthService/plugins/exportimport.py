##############################################################################
#
# Copyright (c) 2005 Zope Foundation and Contributors
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
""" Export / import adapters for stock PAS plugins.

TODO:

 o Add export / import adapters for all stock plugin types:

   - [X] ChallengeProtocolChooser (ChallengeProtocolChooserExportImport)

   - [X] CookieAuthHelper (CookieAuthHelperExportImport)

   - [X] DelegatingMultiPlugin (DelegatePathExportImport)

   - [X] DomainAuthHelper (DomainAuthHelperExportImport)

   - [X] DynamicGroupsPlugin (DynamicGroupsPluginExportImport)

   - [X] HTTPBasicAuthHelper (TitleOnlyExportImport)

   - [X] InlineAuthHelper (TitleOnlyExportImport)

   - [X] LocalRolePlugin (TitleOnlyExportImport)

   - [X] NotCompetent_byRoles (NotCompetent_byRolesExportImport)

   - [X] RecursiveGroupsPlugin (TitleOnlyExportImport)

   - [X] RequestTypeSniffer (TitleOnlyExportImport)

   - [X] ScriptablePlugin (ScriptablePluginExportImport)

   - [X] SearchPrincipalsPlugin (DelegatePathExportImport)

   - [X] SessionAuthHelper (TitleOnlyExportImport)

   - [X] ZODBGroupsManager (ZODBGroupManagerExportImport)

   - [X] ZODBRolesManager (ZODBRoleManagerExportImport)

   - [X] ZODBUserManager (ZODBUserManagerExportImport)

 o Review BasePlugin to ensure we haven't left anything out.

$Id$
"""
import sys
import os
from xml.dom.minidom import parseString
from Acquisition import Implicit
from zope.interface import implementer
from Products.GenericSetup.interfaces import IFilesystemExporter
from Products.GenericSetup.interfaces import IFilesystemImporter
from Products.GenericSetup.content import DAVAwareFileAdapter
from Products.GenericSetup.content import FolderishExporterImporter
from Products.GenericSetup.utils import PageTemplateResource


def getPackagePath(instance):
    module = sys.modules[instance.__module__]
    return os.path.dirname(module.__file__)


@implementer(IFilesystemExporter, IFilesystemImporter)
class SimpleXMLExportImport(Implicit):
    """ Base for plugins whose configuration can be dumped to an XML file.

    o Derived classes must define:

      '_FILENAME' -- a class variable naming the export template

      '_getExportInfo' --  a method returning a mapping which will be passed
       to the template as 'info'.

      '_ROOT_TAGNAME' -- the name of the root tag in the XML (for sanity check)

      '_purgeContext' -- a method which clears our context.

      '_updateFromDOM' -- a method taking the root node of the DOM.
    """
    encoding = None

    def __init__(self, context):
        self.context = context

    def export(self, export_context, subdir, root=False):
        """ See IFilesystemExporter.
        """
        package_path = getPackagePath(self)
        template = PageTemplateResource('xml/%s' % self._FILENAME,
                                        package_path).__of__(self.context)
        info = self._getExportInfo()
        export_context.writeDataFile(
            '%s.xml' % self.context.getId(),
            template(info=info).encode('utf-8'),
            'text/xml',
            subdir,
        )

    def listExportableItems(self):
        """ See IFilesystemExporter.
        """
        return ()

    def import_(self, import_context, subdir, root=False):
        """ See IFilesystemImporter
        """
        self.encoding = import_context.getEncoding()

        if import_context.shouldPurge():
            self._purgeContext()

        data = import_context.readDataFile('%s.xml' % self.context.getId(),
                                           subdir).decode('utf-8')

        if data is not None:

            dom = parseString(data)
            root = dom.firstChild
            assert root.tagName == self._ROOT_TAGNAME

            self.context.title = self._getNodeAttr(root, 'title', None)
            self._updateFromDOM(root)

    def _getNodeAttr(self, node, attrname, default=None):
        attr = node.attributes.get(attrname)
        if attr is None:
            return default
        value = attr.value
        if isinstance(value, unicode) and self.encoding is not None:
            value = value.encode(self.encoding)
        return value


@implementer(IFilesystemExporter, IFilesystemImporter)
class ZODBUserManagerExportImport(SimpleXMLExportImport):
    """ Adapter for dumping / loading ZODBUSerManager to an XML file.
    """
    _FILENAME = 'zodbusers.xml'
    _ROOT_TAGNAME = 'zodb-users'

    def _purgeContext(self):
        self.context.__init__(self.context.id, self.context.title)

    def _updateFromDOM(self, root):
        for user in root.getElementsByTagName('user'):
            user_id = self._getNodeAttr(user, 'user_id', None)
            login_name = self._getNodeAttr(user, 'login_name', None)
            password_hash = self._getNodeAttr(user, 'password_hash', None)

            if user_id is None or login_name is None or password_hash is None:
                raise ValueError('Invalid user record')

            self.context.addUser(user_id, login_name, 'x')
            self.context._user_passwords[user_id] = password_hash

    def _getExportInfo(self):
        user_info = []

        for uinfo in self.context.listUserInfo():
            user_id = uinfo['user_id']

            info = {
                'user_id': user_id,
                'login_name': uinfo['login_name'],
                'password_hash': self.context._user_passwords[user_id],
            }

            user_info.append(info)

        return {
            'title': self.context.title,
            'users': user_info,
        }


class ZODBGroupManagerExportImport(SimpleXMLExportImport):
    """ Adapter for dumping / loading ZODBGroupManager to an XML file.
    """
    _FILENAME = 'zodbgroups.xml'
    _ROOT_TAGNAME = 'zodb-groups'

    def _purgeContext(self):
        self.context.__init__(self.context.id, self.context.title)

    def _updateFromDOM(self, root):

        for group in root.getElementsByTagName('group'):
            group_id = self._getNodeAttr(group, 'group_id', None)
            title = self._getNodeAttr(group, 'title', None)
            description = self._getNodeAttr(group, 'description', None)

            self.context.addGroup(group_id, title, description)

            for principal in group.getElementsByTagName('principal'):
                principal_id = self._getNodeAttr(
                    principal,
                    'principal_id',
                    None
                )
                self.context.addPrincipalToGroup(principal_id, group_id)

    def _getExportInfo(self):
        group_info = []
        for ginfo in self.context.listGroupInfo():
            group_id = ginfo['id']
            info = {
                'group_id': group_id,
                'title': ginfo['title'],
                'description': ginfo['description'],
            }
            info['principals'] = self._listGroupPrincipals(group_id)
            group_info.append(info)
        return {
            'title': self.context.title,
            'groups': group_info,
        }

    def _listGroupPrincipals(self, group_id):
        """ List the principal IDs of the group's members.
        """
        result = []
        for k, v in self.context._principal_groups.items():
            if group_id in v:
                result.append(k)
        return tuple(result)


class ZODBRoleManagerExportImport(SimpleXMLExportImport):
    """ Adapter for dumping / loading ZODBGroupManager to an XML file.
    """
    _FILENAME = 'zodbroles.xml'
    _ROOT_TAGNAME = 'zodb-roles'

    def _purgeContext(self):
        self.context.__init__(self.context.id, self.context.title)

    def _updateFromDOM(self, root):
        for role in root.getElementsByTagName('role'):
            role_id = self._getNodeAttr(role, 'role_id', None)
            title = self._getNodeAttr(role, 'title', None)
            description = self._getNodeAttr(role, 'description', None)

            try:
                self.context.addRole(role_id, title, description)
            except KeyError:
                # it's fine if the role already exists
                pass

            for principal in role.getElementsByTagName('principal'):
                principal_id = self._getNodeAttr(
                    principal,
                    'principal_id',
                    None
                )
                self.context.assignRoleToPrincipal(role_id, principal_id)

    def _getExportInfo(self):
        role_info = []

        for rinfo in self.context.listRoleInfo():
            role_id = rinfo['id']
            info = {
                'role_id': role_id,
                'title': rinfo['title'],
                'description': rinfo['description'],
            }
            info['principals'] = self._listRolePrincipals(role_id)
            role_info.append(info)

        return {
            'title': self.context.title,
            'roles': role_info,
        }

    def _listRolePrincipals(self, role_id):
        """ List the principal IDs of the group's members.
        """
        result = []
        for k, v in self.context._principal_roles.items():
            if role_id in v:
                result.append(k)
        return tuple(result)


class CookieAuthHelperExportImport(SimpleXMLExportImport):
    """ Adapter for dumping / loading CookieAuthHelper to an XML file.
    """
    _FILENAME = 'cookieauth.xml'
    _ROOT_TAGNAME = 'cookie-auth'

    def _purgeContext(self):
        pass

    def _updateFromDOM(self, root):
        cookie_name = self._getNodeAttr(root, 'cookie_name', None)
        if cookie_name is not None:
            self.context.cookie_name = cookie_name
        else:
            try:
                del self.context.cookie_name
            except AttributeError:
                pass

        login_path = self._getNodeAttr(root, 'login_path', None)
        if login_path is not None:
            self.context.login_path = login_path
        else:
            try:
                del self.context.login_path
            except AttributeError:
                pass

    def _getExportInfo(self):
        return {
            'title': self.context.title,
            'cookie_name': self.context.cookie_name,
            'login_path': self.context.login_path,
        }


class DomainAuthHelperExportImport(SimpleXMLExportImport):
    """ Adapter for dumping / loading DomainAuthHelper to an XML file.
    """
    _FILENAME = 'domainauth.xml'
    _ROOT_TAGNAME = 'domain-auth'

    def _purgeContext(self):
        self.context.__init__(self.context.id, self.context.title)

    def _updateFromDOM(self, root):
        for user in root.getElementsByTagName('user'):
            user_id = self._getNodeAttr(user, 'user_id', None)

            for match in user.getElementsByTagName('match'):
                username = self._getNodeAttr(match, 'username', None)
                match_type = self._getNodeAttr(match, 'match_type', None)
                match_string = self._getNodeAttr(match, 'match_string', None)
                role_tokens = self._getNodeAttr(match, 'roles', None)
                roles = role_tokens.split(',')

                self.context.manage_addMapping(
                    user_id=user_id,
                    match_type=match_type,
                    match_string=match_string,
                    username=username,
                    roles=roles,
                )

    def _getExportInfo(self):
        user_map = {}
        for k, v in self.context._domain_map.items():
            user_map[k] = matches = []
            for match in v:
                match = match.copy()
                match['roles'] = ','.join(match['roles'])
                matches.append(match)

        return {
            'title': self.context.title,
            'map': user_map
        }


class TitleOnlyExportImport(SimpleXMLExportImport):
    """ Adapter for dumping / loading title-only plugins to an XML file.
    """
    _FILENAME = 'titleonly.xml'
    _ROOT_TAGNAME = 'plug-in'

    def _purgeContext(self):
        pass

    def _updateFromDOM(self, root):
        pass

    def _getExportInfo(self):
        return {'title': self.context.title, }


class DelegatePathExportImport(SimpleXMLExportImport):
    """ Adapter for dumping / loading plugins with 'delegate' via XML.
    """
    _FILENAME = 'delegatepath.xml'
    _ROOT_TAGNAME = 'delegating-plugin'

    def _purgeContext(self):
        pass

    def _updateFromDOM(self, root):
        delegate = self._getNodeAttr(root, 'delegate', None)
        if delegate is not None:
            self.context.delegate = delegate
        else:
            try:
                del self.context.delegate
            except AttributeError:
                pass

    def _getExportInfo(self):
        return {
            'title': self.context.title,
            'delegate': self.context.delegate,
        }


class DynamicGroupsPluginExportImport(SimpleXMLExportImport):
    """ Adapter for dumping / loading DynamicGroupsPlugin to an XML file.
    """
    _FILENAME = 'dynamicgroups.xml'
    _ROOT_TAGNAME = 'dynamic-groups'

    def _purgeContext(self):
        for group_id in self.context.listGroupIds():
            self.context.removeGroup(group_id)

    def _updateFromDOM(self, root):
        for group in root.getElementsByTagName('group'):
            group_id = self._getNodeAttr(group, 'group_id', None)
            predicate = self._getNodeAttr(group, 'predicate', None)
            title = self._getNodeAttr(group, 'title', None)
            description = self._getNodeAttr(group, 'description', None)
            active = self._getNodeAttr(group, 'active', None)

            self.context.addGroup(
                group_id,
                predicate,
                title,
                description,
                active == 'True',
            )

    def _getExportInfo(self):
        group_info = []

        for ginfo in self.context.listGroupInfo():
            group_id = ginfo['id']
            info = {
                'group_id': group_id,
                'predicate': ginfo['predicate'],
                'title': ginfo['title'],
                'description': ginfo['description'],
                'active': ginfo['active'],
            }
            group_info.append(info)

        return {
            'title': self.context.title,
            'groups': group_info,
        }


class ChallengeProtocolChooserExportImport(SimpleXMLExportImport):
    """ Adapter for dumping / loading ChallengeProtocolChooser to an XML file.
    """
    _FILENAME = 'chooser.xml'
    _ROOT_TAGNAME = 'challenge-protocol-chooser'

    def _purgeContext(self):
        self.context._map.clear()

    def _updateFromDOM(self, root):
        for mapping in root.getElementsByTagName('mapping'):
            label = self._getNodeAttr(mapping, 'label', None)
            protocols = self._getNodeAttr(mapping, 'protocols', '').split(',')
            self.context._map[label] = tuple(filter(None, protocols))

    def _getExportInfo(self):
        from Products.PluggableAuthService.plugins.ChallengeProtocolChooser \
            import listRequestTypesLabels

        request_type_info = []

        for label in sorted(listRequestTypesLabels()):
            protocols = sorted(self.context._map.get(label, []))
            request_type_info.append({
                'label': label,
                'protocols': protocols,
            })

        return {
            'title': self.context.title,
            'request_types': request_type_info,
        }


class ScriptablePluginExportImport(FolderishExporterImporter):
    """ Export / import the Scriptable type plugin.
    """
    def export(self, export_context, subdir, root=False):
        """ See IFilesystemExporter.
        """
        FolderishExporterImporter.export(self, export_context, subdir, root)

    def import_(self, import_context, subdir, root=False):
        """ See IFilesystemImporter.
        """
        FolderishExporterImporter.import_(self, import_context, subdir, root)


class PythonScriptFileAdapter(DAVAwareFileAdapter):
    """File-ish for PythonScript.
    """
    def _getFileName(self):
        """ Return the name under which our file data is stored.
        """
        return '%s.py' % self.context.getId()


class NotCompetent_byRolesExportImport(SimpleXMLExportImport):
    """ Adapter for dumping / loading NCbR plugin.
    """
    _FILENAME = 'notcompetent.xml'
    _ROOT_TAGNAME = 'not-competent-by-roles'

    def _purgeContext(self):
        pass

    def _updateFromDOM(self, root):
        roles = []
        for node in root.getElementsByTagName('role'):
            role = node.firstChild.wholeText
            roles.append(role.strip())
        self.context.roles = tuple(roles)

    def _getExportInfo(self):
        return {
            'title': self.context.title,
            'roles': self.context.roles,
        }
