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
import unittest

from OFS.Folder import Folder
from OFS.SimpleItem import SimpleItem
from zope.interface import Interface
from zope.interface import providedBy


class IFaux(Interface):

    def faux_method():
        """faux_method"""


class IFauxTwo(Interface):

    def two_method():
        """two_method"""


class DummyPluginRegistry(Folder):

    def listPluginIds(self, interface):
        return ()

    def _getInterfaceFromName(self, name):
        if name == 'IFaux':
            return IFaux
        assert name == 'IFauxTwo'
        return IFauxTwo


class ScriptablePluginTests(unittest.TestCase):

    def _getTargetClass(self):

        from ...plugins.ScriptablePlugin import ScriptablePlugin

        return ScriptablePlugin

    def _makeOne(self, id='test', *args, **kw):

        return self._getTargetClass()(id=id, *args, **kw)

    def test_empty(self):

        scriptable_plugin = self._makeOne()
        self.assertNotIn(IFaux, providedBy(scriptable_plugin))
        self.assertNotIn(IFauxTwo, providedBy(scriptable_plugin))

    def test_withTwo(self):

        parent = Folder()
        parent._setObject('plugins', DummyPluginRegistry())

        scriptable_plugin = self._makeOne().__of__(parent)

        faux_method = SimpleItem('faux_method')
        two_method = SimpleItem('two_method')

        scriptable_plugin._setObject('faux_method', faux_method)
        scriptable_plugin._setObject('two_method', two_method)

        scriptable_plugin.manage_updateInterfaces(['IFaux', 'IFauxTwo'])

        self.assertIn(IFaux, providedBy(scriptable_plugin))
        self.assertIn(IFauxTwo, providedBy(scriptable_plugin))

    def test_withTwoOnlyOneWired(self):

        parent = Folder()
        parent._setObject('plugins', DummyPluginRegistry())

        scriptable_plugin = self._makeOne().__of__(parent)

        faux_method = SimpleItem('faux_method')
        whatever = SimpleItem('whatever')

        scriptable_plugin._setObject('faux_method', faux_method)
        scriptable_plugin._setObject('whatever', whatever)

        scriptable_plugin.manage_updateInterfaces(['IFaux'])

        self.assertIn(IFaux, providedBy(scriptable_plugin))

    def test_withTwoMinusOne(self):

        parent = Folder()
        parent._setObject('plugins', DummyPluginRegistry())

        scriptable_plugin = self._makeOne().__of__(parent)

        faux_method = SimpleItem('faux_method')
        two_method = SimpleItem('two_method')

        scriptable_plugin._setObject('faux_method', faux_method)
        scriptable_plugin._setObject('two_method', two_method)

        scriptable_plugin.manage_updateInterfaces(['IFaux', 'IFauxTwo'])

        scriptable_plugin._delObject('two_method')

        self.assertIn(IFaux, providedBy(scriptable_plugin))
        self.assertNotIn(IFauxTwo, providedBy(scriptable_plugin))
