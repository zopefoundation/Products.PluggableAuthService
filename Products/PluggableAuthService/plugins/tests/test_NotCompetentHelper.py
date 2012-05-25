##############################################################################
#
# Copyright (c) 2012 Zope Foundation and Contributors
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
import unittest

from ZPublisher.BaseRequest import UNSPECIFIED_ROLES

from Products.PluggableAuthService.tests.conformance \
     import INotCompetentPlugin_conformance
from Products.PluggableAuthService.tests.test_PluggableAuthService \
     import PluggableAuthServiceTests



class _WrapPluggableAuthServiceTests( PluggableAuthServiceTests ):
    """auxiliary wrapper class to allow for instantiation."""

    def __init__(self, *args, **kw): pass



class NotCompetentHelperTests( unittest.TestCase
                           , INotCompetentPlugin_conformance
                           ):

    def _getTargetClass( self ):

        from Products.PluggableAuthService.plugins.NotCompetentHelper \
            import NotCompetent_byRoles

        return NotCompetent_byRoles

    def _makeOne( self, id='test', *args, **kw ):

        return self._getTargetClass()( id=id, *args, **kw )

    def setUp( self ):
        # we use `PluggableAuthServiceTests` to set up a structure
        #  with two pas instances: one at the root set up for
        #  authentications, the other further down with a
        #  `NotCompetent_byRoles` plugin.
        past = _WrapPluggableAuthServiceTests( )
        root_pas, request = past._setup_for_authentication( )
        request.roles = UNSPECIFIED_ROLES
        request._auth = None
        request.response = None
        root = request[ "PARENTS" ][ -1 ]
        root._setObject(root_pas.getId(), root_pas)
        test_pas = past._makeOne( past._makePlugins( ) )
        folder = request[ "PARENTS" ][ -2 ]
        folder._setObject(test_pas.getId(), test_pas)
        test_pas = folder._getOb( test_pas.getId( ) ) # ac wrap
        nc = self._getTargetClass()( "nc" )
        test_pas._setObject( nc.getId(), nc )
        self.plugin, self.request = test_pas._getOb( nc.getId( ) ), request

    def test__generateHigherLevelUserFolders( self ):
        plugin = self.plugin
        self.assertEqual( len( list( plugin._generateHigherLevelUserFolders( ) ) ), 1)

    def test__getHigherLevelUser( self ):
        plugin, request = self.plugin, self.request
        hlu =  plugin._getHigherLevelUser( request )
        self.assertEqual( hlu.getUserName( ), "olivier" )

    def test__getHigherLevelUser_asHamlet( self ):
        plugin, request = self.plugin, self.request
        hlu =  plugin._getHigherLevelUser( request, ( "Hamlet", ) )
        self.assertEqual( hlu.getUserName( ), "olivier" )

    def test__getHigherLevelUser_asManager( self ):
        plugin, request = self.plugin, self.request
        hlu =  plugin._getHigherLevelUser( request, ( "Manager", ) )
        self.assertEqual( hlu, None)

    def test__getHigherLevelUser_requiresHamlet( self ):
        plugin, request = self.plugin, self.request
        request.roles =  ( "Hamlet", )
        hlu =  plugin._getHigherLevelUser( request )
        self.assertEqual( hlu.getUserName( ), "olivier" )

    def test__getHigherLevelUser_requiresManager( self ):
        plugin, request = self.plugin, self.request
        request.roles =  ( "Manager", )
        hlu =  plugin._getHigherLevelUser( request )
        self.assertEqual( hlu, None)

    def test_isNotCompetent_any( self ):
        plugin, request = self.plugin, self.request
        self.assertEqual( plugin.isNotCompetentToAuthenticate( request ),
                          True
                          )

    def test_isNotCompetent_Hamlet( self ):
        plugin, request = self.plugin, self.request
        plugin.manage_changeProperties( roles=( "Hamlet", ) )
        self.assertEqual( plugin.isNotCompetentToAuthenticate( request ),
                          True
                          )

    def test_isNotCompetent_Manager( self ):
        plugin, request = self.plugin, self.request
        plugin.manage_changeProperties( roles=( "Manager", ) )
        self.assertEqual( plugin.isNotCompetentToAuthenticate( request ),
                          False
                          )


if __name__ == "__main__":
    unittest.main()

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite( NotCompetentHelperTests ),
        ))




