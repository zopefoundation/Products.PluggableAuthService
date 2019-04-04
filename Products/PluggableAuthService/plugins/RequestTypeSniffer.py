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
""" Classes: RequestTypeSniffer
"""

from AccessControl import ClassSecurityInfo
from AccessControl.class_init import InitializeClass
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from zope.interface import Interface
from ZPublisher import xmlrpc

from Products.PluggableAuthService import HAVE_ZSERVER
from Products.PluggableAuthService.interfaces.plugins import \
    IRequestTypeSniffer
from Products.PluggableAuthService.interfaces.request import IBrowserRequest
from Products.PluggableAuthService.interfaces.request import IWebDAVRequest
from Products.PluggableAuthService.interfaces.request import IXMLRPCRequest
from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin
from Products.PluggableAuthService.utils import classImplements


if HAVE_ZSERVER:
    from ZServer.FTPRequest import FTPRequest
    from Products.PluggableAuthService.interfaces.request import IFTPRequest


class IRequestTypeSnifferPlugin(Interface):
    """ Marker interface.
    """


_sniffers = ()


def registerSniffer(iface, func):
    global _sniffers
    registry = list(_sniffers)
    registry.append((iface, func))
    _sniffers = tuple(registry)


manage_addRequestTypeSnifferForm = PageTemplateFile(
    'www/rtsAdd', globals(), __name__='manage_addRequestTypeSnifferForm')


def addRequestTypeSnifferPlugin(dispatcher, id, title=None, REQUEST=None):
    """ Add a RequestTypeSnifferPlugin to a Pluggable Auth Service. """

    rts = RequestTypeSniffer(id, title)
    dispatcher._setObject(rts.getId(), rts)

    if REQUEST is not None:
        REQUEST['RESPONSE'].redirect('%s/manage_workspace'
                                     '?manage_tabs_message='
                                     'RequestTypeSniffer+added.' %
                                     dispatcher.absolute_url())


class RequestTypeSniffer(BasePlugin):

    """ PAS plugin for detecting a Request's type
    """
    meta_type = 'Request Type Sniffer Plugin'
    zmi_icon = 'fas fa-broadcast-tower'

    security = ClassSecurityInfo()

    def __init__(self, id, title=None):

        self._id = self.id = id
        self.title = title

    @security.private
    def sniffRequestType(self, request):
        found = None
        for iface, func in _sniffers:
            if func(request):
                found = iface

        if found is not None:
            return found


classImplements(RequestTypeSniffer, IRequestTypeSnifferPlugin,
                IRequestTypeSniffer)


InitializeClass(RequestTypeSniffer)

if HAVE_ZSERVER:
    # Most of the sniffing code below has been inspired by
    # similar tests found in BaseRequest, HTTPRequest and ZServer
    def webdavSniffer(request):
        dav_src = request.get('WEBDAV_SOURCE_PORT', None)
        method = request.get('REQUEST_METHOD', 'GET').upper()
        path_info = request.get('PATH_INFO', '')

        if dav_src:
            return True

        if method not in ('GET', 'POST'):
            return True

        if method in ('GET',) and path_info.endswith('manage_DAVget'):
            return True

    registerSniffer(IWebDAVRequest, webdavSniffer)

    def ftpSniffer(request):
        if isinstance(request, FTPRequest):
            return True

    registerSniffer(IFTPRequest, ftpSniffer)


def xmlrpcSniffer(request):
    response = request['RESPONSE']
    method = request.get('REQUEST_METHOD', 'GET').upper()

    if method in ('GET', 'POST') and isinstance(response, xmlrpc.Response):
        return True


registerSniffer(IXMLRPCRequest, xmlrpcSniffer)


def browserSniffer(request):
    # If it's none of the above, it's very likely a browser request.
    if xmlrpcSniffer(request):
        return False
    elif not HAVE_ZSERVER:
        return True

    for sniffer in (webdavSniffer, ftpSniffer):
        if sniffer(request):
            return False

    return True


registerSniffer(IBrowserRequest, browserSniffer)
