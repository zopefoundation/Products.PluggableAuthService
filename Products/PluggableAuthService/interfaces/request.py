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
"""
# Eventually, those interfaces should be moved to Zope and imported
# here as aliases for backward compatibility.

from zope.interface import Interface


class IRequest(Interface):

    """ Base Request Interface

    ??? Add methods from BaseRequest?
    """


class IHTTPRequest(IRequest):

    """ HTTP Request
    """


class IBrowserRequest(IHTTPRequest):

    """Browser Request
    """


class IWebDAVRequest(IHTTPRequest):

    """ WebDAV Request
    """


class IXMLRPCRequest(IHTTPRequest):

    """ XML-RPC Request
    """


class IFTPRequest(IRequest):

    """ FTP Request
    """
