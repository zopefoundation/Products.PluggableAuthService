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
""" Class: SessionAuthHelper
"""

from AccessControl.class_init import InitializeClass
from AccessControl.SecurityInfo import ClassSecurityInfo
from OFS.PropertyManager import PropertyManager
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from zope.event import notify
from zope.interface import Interface

from ..events import UserSessionStarted
from ..interfaces.plugins import ICredentialsResetPlugin
from ..interfaces.plugins import ICredentialsUpdatePlugin
from ..interfaces.plugins import ILoginPasswordHostExtractionPlugin
from ..plugins.BasePlugin import BasePlugin
from ..utils import classImplements


class ISessionAuthHelper(Interface):
    """ Marker interface.
    """


manage_addSessionAuthHelperForm = PageTemplateFile(
    'www/saAdd', globals(), __name__='manage_addSessionAuthHelperForm')


def manage_addSessionAuthHelper(dispatcher, id, title=None, REQUEST=None):
    """ Add a Session Auth Helper to a Pluggable Auth Service. """
    sp = SessionAuthHelper(id, title)
    dispatcher._setObject(sp.getId(), sp)

    if REQUEST is not None:
        REQUEST['RESPONSE'].redirect('%s/manage_workspace'
                                     '?manage_tabs_message='
                                     'SessionAuthHelper+added.' %
                                     dispatcher.absolute_url())


class SessionAuthHelper(BasePlugin):
    """ Multi-plugin for managing details of Session Authentication. """
    meta_type = 'Session Auth Helper'
    zmi_icon = 'fas fa-fingerprint'
    security = ClassSecurityInfo()
    clear_session_on_login = False

    _properties = (
        PropertyManager._properties +
        ({'id': 'clear_session_on_login',
          'label': 'Clear session data at login boundary',
          'type': 'boolean',
          'mode': 'rw'},)
    )

    def __init__(self, id, title=None):
        self._setId(id)
        self.title = title

    @security.private
    def extractCredentials(self, request):
        """ Extract basic auth credentials from 'request'. """
        creds = {}

        # Looking into the session first...
        name = request.SESSION.get('__ac_name', '')
        password = request.SESSION.get('__ac_password', '')

        if name:
            creds['login'] = name
            creds['password'] = password
        else:
            # Look into the request now
            login_pw = request._authUserPW()

            if login_pw is not None:
                name, password = login_pw
                creds['login'] = name
                creds['password'] = password

                # Put the newly discovered credentials into the user session
                self.updateCredentials(
                    request, request.RESPONSE, name, password)

        if creds:
            creds['remote_host'] = request.get('REMOTE_HOST', '')

            try:
                creds['remote_address'] = request.getClientAddr()
            except AttributeError:
                creds['remote_address'] = request.get('REMOTE_ADDR', '')

        return creds

    @security.private
    def updateCredentials(self, request, response, login, new_password):
        """ Respond to change of credentials. """
        if request.SESSION.get('__ac_name') != login:
            # This is a new session, notify.
            notify(UserSessionStarted(login))
            if self.clear_session_on_login:
                request.SESSION.clear()
            request.SESSION.set('__ac_name', login)
        request.SESSION.set('__ac_password', new_password)

    @security.private
    def resetCredentials(self, request, response):
        """ Empty out the currently-stored session values """
        request.SESSION.set('__ac_name', '')
        request.SESSION.set('__ac_password', '')


classImplements(SessionAuthHelper, ISessionAuthHelper,
                ILoginPasswordHostExtractionPlugin, ICredentialsUpdatePlugin,
                ICredentialsResetPlugin)

InitializeClass(SessionAuthHelper)
