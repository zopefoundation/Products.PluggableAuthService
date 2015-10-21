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
""" Classes: ChallengeProtocolChooser

$Id$
"""
from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass
from BTrees.OOBTree import OOBTree
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.PluggableAuthService.interfaces import plugins as iplugins
from Products.PluggableAuthService.interfaces import request as irequest
from Products.PluggableAuthService.plugins.RequestTypeSniffer \
    import IRequestTypeSniffer
from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin
from zope.interface import implementer
from zope.interface import Interface
from zope.publisher.interfaces.browser import IBrowserRequest
from zope.publisher.interfaces.ftp import IFTPRequest
from zope.publisher.interfaces.xmlrpc import IXMLRPCRequest


class IChallengeProtocolChooserPlugin(Interface):
    """ Marker interface.
    """

_request_types = ()
_request_type_bmap = {}


def registerRequestType(label, iface):
    global _request_types
    registry = list(_request_types)
    registry.append((label, iface))
    _request_types = tuple(registry)
    _request_type_bmap[iface] = label


def listRequestTypesLabels():
    return _request_type_bmap.values()

manage_addChallengeProtocolChooserForm = PageTemplateFile(
    'www/cpcAdd', globals(), __name__='manage_addChallengeProtocolChooserForm')


def addChallengeProtocolChooserPlugin(dispatcher, id, title=None,
                                      mapping=None, REQUEST=None):
    """ Add a ChallengeProtocolChooserPlugin to a Pluggable Auth Service. """

    cpc = ChallengeProtocolChooser(id, title=title, mapping=mapping)
    dispatcher._setObject(cpc.getId(), cpc)

    if REQUEST is not None:
        REQUEST['RESPONSE'].redirect(
            '%s/manage_workspace'
            '?manage_tabs_message='
            'ChallengeProtocolChooser+added.'
            % dispatcher.absolute_url())


@implementer(
    IChallengeProtocolChooserPlugin,
    iplugins.IChallengeProtocolChooser
)
class ChallengeProtocolChooser(BasePlugin):

    """ PAS plugin for choosing challenger protocol based on request
    """
    meta_type = 'Challenge Protocol Chooser Plugin'

    security = ClassSecurityInfo()

    manage_options = (({'label': 'Mapping',
                        'action': 'manage_editProtocolMapping'
                        },
                       )
                      + BasePlugin.manage_options
                      )

    def __init__(self, id, title=None, mapping=None):
        self._id = self.id = id
        self.title = title
        self._map = OOBTree()
        if mapping is not None:
            self.manage_updateProtocolMapping(mapping=mapping)

    security.declarePrivate('chooseProtocols')

    def chooseProtocols(self, request):
        pas_instance = self._getPAS()
        plugins = pas_instance._getOb('plugins')

        sniffers = plugins.listPlugins(IRequestTypeSniffer)

        for sniffer_id, sniffer in sniffers:
            request_type = sniffer.sniffRequestType(request)
            if request_type is not None:
                return self._getProtocolsFor(request_type)

    def _getProtocolsFor(self, request_type):
        label = _request_type_bmap.get(request_type, None)
        if label is None:
            return
        return self._map.get(label, None)

    def _listProtocols(self):
        pas_instance = self._getPAS()
        plugins = pas_instance._getOb('plugins')

        challengers = plugins.listPlugins(iplugins.IChallengePlugin)
        found = []

        for challenger_id, challenger in challengers:
            protocol = getattr(challenger, 'protocol', challenger_id)
            if protocol not in found:
                found.append(protocol)

        return found

    manage_editProtocolMappingForm = PageTemplateFile(
        'www/cpcEdit', globals(),
        __name__='manage_editProtocolMappingForm')

    def manage_editProtocolMapping(self, REQUEST=None):
        """ Edit Protocol Mapping
        """
        info = []
        available_protocols = self._listProtocols()

        request_types = listRequestTypesLabels()
        request_types.sort()

        for label in request_types:
            settings = []
            select_any = False
            info.append(
                {'label': label,
                 'settings': settings
                 })
            protocols = self._map.get(label, None)
            if not protocols:
                select_any = True
            for protocol in available_protocols:
                selected = False
                if protocols and protocol in protocols:
                    selected = True
                settings.append({'label': protocol,
                                 'selected': selected,
                                 'value': protocol,
                                 })

            settings.insert(0, {'label': '(any)',
                                'selected': select_any,
                                'value': '',
                                })
        return self.manage_editProtocolMappingForm(info=info, REQUEST=REQUEST)

    def manage_updateProtocolMapping(self, mapping, REQUEST=None):
        """ Update mapping of Request Type to Protocols
        """
        for key, value in mapping.items():
            value = filter(None, value)
            if not value:
                if key in self._map:
                    del self._map[key]
            else:
                self._map[key] = value

        if REQUEST is not None:
            REQUEST['RESPONSE'].redirect(
                '%s/manage_editProtocolMapping'
                '?manage_tabs_message='
                'Protocol+Mappings+Changed.'
                % self.absolute_url())


InitializeClass(ChallengeProtocolChooser)

for label, iface in (
    ('Browser', IBrowserRequest),
    ('WebDAV', irequest.IWebDAVRequest),
    ('FTP', IFTPRequest),
    ('XML-RPC', IXMLRPCRequest)
):
    registerRequestType(label, iface)
