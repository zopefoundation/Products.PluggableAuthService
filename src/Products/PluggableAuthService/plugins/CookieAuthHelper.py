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
""" Class: CookieAuthHelper
"""

import codecs
from base64 import decodebytes
from base64 import encodebytes
from binascii import Error
from binascii import hexlify
from urllib.parse import quote
from urllib.parse import unquote

from AccessControl.class_init import InitializeClass
from AccessControl.Permissions import view
from AccessControl.SecurityInfo import ClassSecurityInfo
from Acquisition import aq_inner
from Acquisition import aq_parent
from OFS.Folder import Folder
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate
from zope.event import notify
from zope.interface import Interface

from ..events import UserSessionStarted
from ..interfaces.plugins import IChallengePlugin
from ..interfaces.plugins import ICredentialsResetPlugin
from ..interfaces.plugins import ICredentialsUpdatePlugin
from ..interfaces.plugins import ILoginPasswordHostExtractionPlugin
from ..plugins.BasePlugin import BasePlugin
from ..utils import classImplements
from ..utils import url_local


class ICookieAuthHelper(Interface):
    """ Marker interface.
    """


manage_addCookieAuthHelperForm = PageTemplateFile(
    'www/caAdd', globals(), __name__='manage_addCookieAuthHelperForm')


def addCookieAuthHelper(dispatcher, id, title=None, cookie_name='',
                        REQUEST=None):
    """ Add a Cookie Auth Helper to a Pluggable Auth Service. """
    sp = CookieAuthHelper(id, title, cookie_name)
    dispatcher._setObject(sp.getId(), sp)

    if REQUEST is not None:
        REQUEST['RESPONSE'].redirect('%s/manage_workspace'
                                     '?manage_tabs_message='
                                     'CookieAuthHelper+added.' %
                                     dispatcher.absolute_url())


def decode_cookie(raw):
    value = unquote(raw)
    value = value.encode('utf8')
    value = decodebytes(value)
    value = value.decode('utf8')
    return value


def decode_hex(raw):
    if isinstance(raw, str):
        raw = raw.encode('utf8')
    value = codecs.decode(raw, 'hex_codec')
    value = value.decode('utf-8')
    return value


class CookieAuthHelper(Folder, BasePlugin):
    """ Multi-plugin for managing details of Cookie Authentication. """

    meta_type = 'Cookie Auth Helper'
    zmi_icon = 'fas fa-cookie-bite'
    cookie_name = '__ginger_snap'
    login_path = 'login_form'
    cookie_same_site = 'Lax'
    cookie_same_site_choices = ('None', 'Lax', 'Strict')
    cookie_secure = False
    security = ClassSecurityInfo()

    _properties = ({'id': 'title', 'label': 'Title',
                    'type': 'string', 'mode': 'w'},
                   {'id': 'cookie_name', 'label': 'Cookie Name',
                    'type': 'string', 'mode': 'w'},
                   {'id': 'cookie_secure', 'type': 'boolean', 'mode': 'w',
                    'label': 'Send cookie over HTTPS only'},
                   {'id': 'cookie_same_site', 'type': 'selection',
                    'label': 'Cookie SameSite restriction', 'mode': 'w',
                    'select_variable': 'cookie_same_site_choices'},
                   {'id': 'login_path', 'label': 'Login Form',
                    'type': 'string', 'mode': 'w'})

    manage_options = (BasePlugin.manage_options[:1]
                      + Folder.manage_options[:1]
                      + Folder.manage_options[2:])

    def __init__(self, id, title=None, cookie_name=''):
        self._setId(id)
        self.title = title

        if cookie_name:
            self.cookie_name = cookie_name

    def _getCookieData(self, request):
        cookie_creds = {}
        cookie = request.get(self.cookie_name, '')

        if cookie and cookie != 'deleted':
            try:
                cookie_val = decode_cookie(cookie)
            except Error:
                # Cookie is in a different format, so it is not ours
                return cookie_creds

            try:
                login, password = cookie_val.split(':')
            except ValueError:
                # Cookie is in a different format, so it is not ours
                return cookie_creds

            try:
                cookie_creds['login'] = decode_hex(login)
                cookie_creds['password'] = decode_hex(password)
            except (Error, TypeError):
                # Cookie is in a different format, so it is not ours
                return cookie_creds

        return cookie_creds

    @security.private
    def extractCredentials(self, request):
        """ Extract credentials from cookie or 'request'. """
        creds = {}
        # Look in the request.form for the names coming from the login form
        login = request.form.get('__ac_name', '')

        if login and '__ac_password' in request.form:
            creds['login'] = login
            creds['password'] = request.form.get('__ac_password', '')
        else:
            creds = self._getCookieData(request)

        if creds:
            creds['remote_host'] = request.get('REMOTE_HOST', '')

            try:
                creds['remote_address'] = request.getClientAddr()
            except AttributeError:
                creds['remote_address'] = request.get('REMOTE_ADDR', '')

        return creds

    @security.private
    def challenge(self, request, response, **kw):
        """ Challenge the user for credentials. """
        return self.unauthorized()

    @security.private
    def get_cookie_value(self, login, new_password):
        cookie_str = b':'.join([
            hexlify(login.encode('utf-8')),
            hexlify(new_password.encode('utf-8'))])
        cookie_val = encodebytes(cookie_str)
        cookie_val = cookie_val.rstrip()
        return cookie_val

    @security.private
    def updateCredentials(self, request, response, login, new_password):
        """ Respond to change of credentials (NOOP for basic auth). """
        old_creds = self._getCookieData(request)
        cookie_val = self.get_cookie_value(login, new_password)
        cookie_secure = self.cookie_same_site == 'None' or self.cookie_secure
        response.setCookie(self.cookie_name, quote(cookie_val),
                           path='/', same_site=self.cookie_same_site,
                           secure=cookie_secure)
        if old_creds.get('login') != login:
            # Only notify if cookie is new or the login changed
            notify(UserSessionStarted(login))

    @security.private
    def resetCredentials(self, request, response):
        """ Raise unauthorized to tell browser to clear credentials. """
        response.expireCookie(self.cookie_name, path='/')

    @security.private
    def manage_afterAdd(self, item, container):
        """ Setup tasks upon instantiation """
        if 'login_form' not in self.objectIds():
            login_form = ZopePageTemplate(id='login_form',
                                          text=BASIC_LOGIN_FORM)
            login_form.title = 'Login Form'
            login_form.manage_permission(view, roles=['Anonymous'], acquire=1)
            self._setObject('login_form', login_form, set_owner=0)

    @security.private
    def unauthorized(self):
        req = self.REQUEST
        resp = req['RESPONSE']

        # If we set the auth cookie before, delete it now.
        if self.cookie_name in resp.cookies:
            del resp.cookies[self.cookie_name]

        # Redirect if desired.
        url = self.getLoginURL()
        if url is not None:
            came_from = req.get('came_from', None)

            if came_from is None:
                came_from = req.get('ACTUAL_URL', '')
                query = req.get('QUERY_STRING')
                if query:
                    if not query.startswith('?'):
                        query = '?' + query
                    came_from = came_from + query
            else:
                # If came_from contains a value it means the user
                # must be coming through here a second time
                # Reasons could be typos when providing credentials
                # or a redirect loop (see below)
                req_url = req.get('ACTUAL_URL', '')

                if req_url and req_url == url:
                    # Oops... The login_form cannot be reached by the user -
                    # it might be protected itself due to misconfiguration -
                    # the only sane thing to do is to give up because we are
                    # in an endless redirect loop.
                    return 0

            # Sanitize the return URL ``came_from`` and only allow local URLs
            # to prevent an open exploitable redirect issue
            came_from = url_local(came_from)

            if '?' in url:
                sep = '&'
            else:
                sep = '?'
            url = f'{url}{sep}came_from={quote(came_from)}'
            resp.redirect(url, lock=1)
            resp.setHeader('Expires', 'Sat, 01 Jan 2000 00:00:00 GMT')
            resp.setHeader('Cache-Control', 'no-cache')
            return 1

        # Could not challenge.
        return 0

    @security.private
    def getLoginURL(self):
        """ Where to send people for logging in """
        if self.login_path.startswith('/') or '://' in self.login_path:
            return self.login_path
        elif self.login_path != '':
            return f'{self.absolute_url()}/{self.login_path}'
        else:
            return None

    @security.public
    def login(self):
        """ Set a cookie and redirect to the url that we tried to
        authenticate against originally.
        """
        request = self.REQUEST
        response = request['RESPONSE']

        login = request.get('__ac_name', '')
        password = request.get('__ac_password', '')

        # In order to use the CookieAuthHelper for its nice login page
        # facility but store and manage credentials somewhere else we need
        # to make sure that upon login only plugins activated as
        # IUpdateCredentialPlugins get their updateCredentials method
        # called. If the method is called on the CookieAuthHelper it will
        # simply set its own auth cookie, to the exclusion of any other
        # plugins that might want to store the credentials.
        pas_instance = self._getPAS()

        if pas_instance is not None:
            pas_instance.updateCredentials(request, response, login, password)
        came_from = request.form.get('came_from')
        if came_from is not None:
            return response.redirect(url_local(came_from))
        # When this happens, this either means
        # - the administrator did not setup the login form properly
        # - the user manipulated the login form and removed `came_from`
        # Still, the user provided correct credentials and is logged in.
        pas_root = aq_parent(aq_inner(self._getPAS()))
        return response.redirect(pas_root.absolute_url())


classImplements(CookieAuthHelper, ICookieAuthHelper,
                ILoginPasswordHostExtractionPlugin, IChallengePlugin,
                ICredentialsUpdatePlugin, ICredentialsResetPlugin)

InitializeClass(CookieAuthHelper)


BASIC_LOGIN_FORM = """<html>
  <head>
    <title> Login Form </title>
  </head>

  <body>

    <h3> Please log in </h3>

    <form method="post" action=""
          tal:attributes="action string:${here/absolute_url}/login">

      <input type="hidden" name="came_from" value=""
             tal:attributes="value request/came_from | string:"/>
      <table cellpadding="2">
        <tr>
          <td><b>Login:</b> </td>
          <td><input type="text" name="__ac_name" size="30" /></td>
        </tr>
        <tr>
          <td><b>Password:</b></td>
          <td><input type="password" name="__ac_password" size="30" /></td>
        </tr>
        <tr>
          <td colspan="2">
            <br />
            <input type="submit" value=" Log In " />
          </td>
        </tr>
      </table>

    </form>

  </body>

</html>
"""
