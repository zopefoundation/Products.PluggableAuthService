# -*- coding: utf-8 -*-
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
""" Interfaces for PluggableAuthService

$Id$
"""
# BBB import, DEPRECATED, remove in 3.1
# XXX not sure how subsitute IWebDAVRequest
from zope.publisher.interfaces import IRequest  # noqa
from zope.publisher.interfaces.browser import IBrowserRequest  # noqa
from zope.publisher.interfaces.ftp import IFTPRequest  # noqa
from zope.publisher.interfaces.http import IHTTPRequest
from zope.publisher.interfaces.xmlrpc import IXMLRPCRequest  # noqa


class IWebDAVRequest(IHTTPRequest):
    """ WebDAV Request
    """
