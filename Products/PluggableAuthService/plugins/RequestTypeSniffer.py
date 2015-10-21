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

$Id$
"""
from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.PluggableAuthService.interfaces.plugins \
    import IRequestTypeSniffer
from Products.PluggableAuthService.interfaces.request import IWebDAVRequest
from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin
from zope.interface import implementer
from zope.interface import Interface
from zope.publisher.interfaces.browser import IBrowserRequest
from zope.publisher.interfaces.ftp import IFTPRequest
from zope.publisher.interfaces.xmlrpc import IXMLRPCRequest
from ZPublisher import xmlrpc
from ZServer.FTPRequest import FTPRequest


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
        REQUEST['RESPONSE'].redirect(
            '%s/manage_workspace'
            '?manage_tabs_message='
            'RequestTypeSniffer+added.'
            % dispatcher.absolute_url())


@implementer(IRequestTypeSnifferPlugin, IRequestTypeSniffer)
class RequestTypeSniffer(BasePlugin):

    """ PAS plugin for detecting a Request's type
    """
    meta_type = 'Request Type Sniffer Plugin'

    security = ClassSecurityInfo()

    def __init__(self, id, title=None):

        self._id = self.id = id
        self.title = title

    security.declarePrivate('sniffRequestType')

    def sniffRequestType(self, request):
        found = None
        for iface, func in _sniffers:
            if func(request):
                found = iface

        if found is not None:
            return found

InitializeClass(RequestTypeSniffer)

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


def xmlrpcSniffer(request):
    response = request['RESPONSE']
    method = request.get('REQUEST_METHOD', 'GET').upper()

    if method in ('GET', 'POST') and isinstance(response, xmlrpc.Response):
        return True

registerSniffer(IXMLRPCRequest, xmlrpcSniffer)


def ftpSniffer(request):
    if isinstance(request, FTPRequest):
        return True

registerSniffer(IFTPRequest, ftpSniffer)


def browserSniffer(request):
    # If it's none of the above, it's very likely a browser request.
    for sniffer in (webdavSniffer, ftpSniffer, xmlrpcSniffer):
        if sniffer(request):
            return False
    return True

registerSniffer(IBrowserRequest, browserSniffer)
