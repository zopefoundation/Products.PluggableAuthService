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

from AccessControl.class_init import InitializeClass
from AccessControl.SecurityInfo import ClassSecurityInfo
from OFS.Folder import Folder
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from zope.interface import Interface

from ..interfaces.plugins import IChallengePlugin
from ..interfaces.plugins import ILoginPasswordHostExtractionPlugin
from ..plugins.BasePlugin import BasePlugin
from ..utils import classImplements


class IInlineAuthHelper(Interface):
    """ Marker interface.
    """


manage_addInlineAuthHelperForm = PageTemplateFile(
    'www/iaAdd', globals(), __name__='manage_addInlineAuthHelperForm')


def addInlineAuthHelper(dispatcher, id, title=None, REQUEST=None):
    """ Add an Inline Auth Helper to a Pluggable Auth Service. """
    iah = InlineAuthHelper(id, title)
    dispatcher._setObject(iah.getId(), iah)

    if REQUEST is not None:
        REQUEST['RESPONSE'].redirect('%s/manage_workspace'
                                     '?manage_tabs_message='
                                     'InlineAuthHelper+added.' %
                                     dispatcher.absolute_url())


class InlineAuthHelper(Folder, BasePlugin):
    """ Multi-plugin for managing details of Inline Authentication. """
    meta_type = 'Inline Auth Helper'
    zmi_icon = 'fas fa-fingerprint'
    security = ClassSecurityInfo()

    _properties = ({'id': 'title', 'label': 'Title',
                    'type': 'string', 'mode': 'w'},)

    manage_options = (BasePlugin.manage_options[:1]
                      + Folder.manage_options[:1]
                      + Folder.manage_options[2:])

    def __init__(self, id, title=None):
        self.id = self._id = id
        self.title = title
        self.body = BASIC_LOGIN_FORM

    @security.private
    def extractCredentials(self, request):
        """ Extract credentials from cookie or 'request'. """
        creds = {}

        # Look in the request for the names coming from the login form
        login = request.get('__ac_name', '')
        password = request.get('__ac_password', '')

        if login:
            creds['login'] = login
            creds['password'] = password

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
        response.setStatus('200')
        response.setHeader('Content-Type', 'text/html')
        response.setBody(self.body)

        # Keep HTTPResponse.exception() from further writing on the
        # response body, without using HTTPResponse.write()
        response._locked_status = True
        response.setBody = self._setBody  # Keep response.exception
        return True

    # Methods to override on response

    def _setBody(self, body, *args, **kw):
        pass


classImplements(InlineAuthHelper, IInlineAuthHelper,
                ILoginPasswordHostExtractionPlugin, IChallengePlugin)

InitializeClass(InlineAuthHelper)


BASIC_LOGIN_FORM = """<html>
  <head>
    <title> Login Form </title>
  </head>

  <body>

    <h3> Please log in </h3>

    <form method="post">
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
