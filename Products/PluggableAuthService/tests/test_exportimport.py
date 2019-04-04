##############################################################################
#
# Copyright (c) 2005 Zope Foundation and Contributors
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this
# distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
""" Unit tests for GenericSetup-based export / import of PAS.
"""
import unittest
from csv import reader

from six import StringIO

from Products.GenericSetup.tests.common import BaseRegistryTests
from zope.component.testing import PlacelessSetup

from Products.PluggableAuthService.tests.utils import _setUpDefaultTraversable


class _TestBase(PlacelessSetup, BaseRegistryTests):

    def _initPAS(self, plugin_type_info=(), plugins={}):
        from OFS.Folder import Folder
        from Products.PluggableAuthService.PluggableAuthService \
            import addPluggableAuthService

        app = Folder()
        app.getPhysicalPath = lambda: ()
        app.getPhysicalRoot = lambda: app

        addPluggableAuthService(app)
        pas = app._getOb('acl_users')

        return app, pas


class Test_exportPAS(_TestBase):

    def _setUpAdapters(self):
        from zope.component import provideAdapter
        from OFS.interfaces import IObjectManager
        from OFS.interfaces import IPropertyManager

        from Products.GenericSetup.interfaces import IContentFactoryName
        from Products.GenericSetup.interfaces import ICSVAware
        from Products.GenericSetup.interfaces import IDAVAware
        from Products.GenericSetup.interfaces import IFilesystemExporter
        from Products.GenericSetup.interfaces import IINIAware
        from Products.GenericSetup.content import \
            FolderishExporterImporter
        from Products.GenericSetup.content import \
            SimpleINIAware
        from Products.GenericSetup.content import \
            CSVAwareFileAdapter
        from Products.GenericSetup.content import \
            INIAwareFileAdapter
        from Products.GenericSetup.content import \
            DAVAwareFileAdapter

        from Products.PluginRegistry.interfaces import IPluginRegistry
        from Products.PluginRegistry.exportimport \
            import PluginRegistryFileExportImportAdapter

        from Products.PluggableAuthService.exportimport \
            import PAS_CF_Namer

        provideAdapter(FolderishExporterImporter,
                       (IObjectManager,),
                       IFilesystemExporter)

        provideAdapter(SimpleINIAware,
                       (IPropertyManager, ),
                       IINIAware)

        provideAdapter(CSVAwareFileAdapter,
                       (ICSVAware, ),
                       IFilesystemExporter)

        provideAdapter(INIAwareFileAdapter,
                       (IINIAware, ),
                       IFilesystemExporter)

        provideAdapter(DAVAwareFileAdapter,
                       (IDAVAware, ),
                       IFilesystemExporter)

        provideAdapter(PluginRegistryFileExportImportAdapter,
                       (IPluginRegistry, ),
                       IFilesystemExporter)

        provideAdapter(PAS_CF_Namer,
                       (IPluginRegistry, ),
                       IContentFactoryName)

    def test_empty(self):
        from Products.GenericSetup.tests.common import DummyExportContext
        from Products.PluggableAuthService.exportimport import exportPAS

        _setUpDefaultTraversable()

        self._setUpAdapters()
        app, pas = self._initPAS()
        context = DummyExportContext(pas)
        exportPAS(context)

        self.assertEqual(len(context._wrote), 3)
        filename, text, content_type = context._wrote[0]
        self.assertEqual(filename, 'PAS/.objects')
        self.assertEqual(content_type, 'text/comma-separated-values')
        self.assertEqual(text.splitlines(),
                         _EMPTY_PAS_OBJECTS.splitlines())

        filename, text, content_type = context._wrote[1]
        self.assertEqual(filename, 'PAS/.properties')
        self.assertEqual(content_type, 'text/plain')
        lines = filter(None, [x.strip() for x in text.splitlines()])
        lines = sorted(lines)
        self.assertEqual(len(lines), 3)
        self.assertEqual(lines[0], '[DEFAULT]')
        self.assertEqual(lines[1], 'login_transform =')
        self.assertEqual(lines[2], 'title =')

        filename, text, content_type = context._wrote[2]
        self.assertEqual(filename, 'PAS/pluginregistry.xml')
        self.assertEqual(content_type, 'text/xml')

    def test_with_contents(self):
        from Products.GenericSetup.tests.common import DummyExportContext
        from Products.GenericSetup.tests.faux_objects \
            import TestCSVAware
        from Products.GenericSetup.utils import _getDottedName
        from Products.PluggableAuthService.exportimport import exportPAS

        _setUpDefaultTraversable()

        self._setUpAdapters()
        app, pas = self._initPAS()
        csv_aware = TestCSVAware()
        csv_aware._setId('csv_plugin')
        pas._setObject('csv_plugin', csv_aware)
        context = DummyExportContext(pas)
        exportPAS(context)

        self.assertEqual(len(context._wrote), 4)
        filename, text, content_type = context._wrote[0]
        self.assertEqual(filename, 'PAS/.objects')
        self.assertEqual(content_type, 'text/comma-separated-values')

        objects = [x for x in reader(StringIO(text))]
        self.assertEqual(len(objects), 2)

        object_id, type_name = objects[0]
        self.assertEqual(object_id, 'plugins')
        self.assertEqual(type_name, 'plugins')  # adapter-driven

        object_id, type_name = objects[1]
        self.assertEqual(object_id, 'csv_plugin')
        self.assertEqual(type_name, _getDottedName(csv_aware.__class__))

        filename, text, content_type = context._wrote[1]
        self.assertEqual(filename, 'PAS/.properties')
        self.assertEqual(content_type, 'text/plain')
        lines = filter(None, [x.strip() for x in text.splitlines()])
        lines = sorted(lines)
        self.assertEqual(len(lines), 3)
        self.assertEqual(lines[0], '[DEFAULT]')
        self.assertEqual(lines[1], 'login_transform =')
        self.assertEqual(lines[2], 'title =')

        filename, text, content_type = context._wrote[2]
        self.assertEqual(filename, 'PAS/pluginregistry.xml')
        self.assertEqual(content_type, 'text/xml')

        filename, text, content_type = context._wrote[3]
        self.assertEqual(filename, 'PAS/csv_plugin.csv')
        self.assertEqual(content_type, 'text/comma-separated-values')


class Test_importPAS(_TestBase):

    def _setUpAdapters(self):
        from zope.component import provideAdapter
        from OFS.interfaces import IObjectManager
        from OFS.interfaces import IPropertyManager

        from Products.GenericSetup.interfaces import IContentFactory
        from Products.GenericSetup.interfaces import ICSVAware
        from Products.GenericSetup.interfaces import IDAVAware
        from Products.GenericSetup.interfaces import IFilesystemImporter
        from Products.GenericSetup.interfaces import IINIAware

        from Products.GenericSetup.content import \
            FolderishExporterImporter
        from Products.GenericSetup.content import \
            SimpleINIAware
        from Products.GenericSetup.content import \
            CSVAwareFileAdapter
        from Products.GenericSetup.content import \
            INIAwareFileAdapter
        from Products.GenericSetup.content import \
            DAVAwareFileAdapter

        from Products.PluginRegistry.interfaces import IPluginRegistry
        from Products.PluginRegistry.exportimport \
            import PluginRegistryFileExportImportAdapter

        from Products.PluggableAuthService.interfaces.authservice \
            import IPluggableAuthService
        from Products.PluggableAuthService.exportimport \
            import PAS_PR_ContentFactory

        provideAdapter(FolderishExporterImporter,
                       (IObjectManager, ),
                       IFilesystemImporter)

        provideAdapter(SimpleINIAware,
                       (IPropertyManager, ),
                       IINIAware)

        provideAdapter(CSVAwareFileAdapter,
                       (ICSVAware, ),
                       IFilesystemImporter)

        provideAdapter(INIAwareFileAdapter,
                       (IINIAware, ),
                       IFilesystemImporter)

        provideAdapter(DAVAwareFileAdapter,
                       (IDAVAware, ),
                       IFilesystemImporter)

        provideAdapter(PluginRegistryFileExportImportAdapter,
                       (IPluginRegistry, ),
                       IFilesystemImporter)

        provideAdapter(PAS_PR_ContentFactory,
                       (IPluggableAuthService, ),
                       IContentFactory,
                       name='plugins')

    def test_empty_modifying_plugin_types(self):
        from Products.GenericSetup.tests.common import DummyImportContext
        from Products.PluggableAuthService.exportimport import importPAS

        self._setUpAdapters()
        app, pas = self._initPAS()

        ctx = DummyImportContext(pas)
        ctx._files['PAS/.objects'] = _EMPTY_PAS_OBJECTS
        ctx._files['PAS/.properties'] = _EMPTY_PAS_PROPERTIES
        ctx._files['PAS/pluginregistry.xml'] = _EMPTY_PLUGINREGISTRY_EXPORT

        self.assertTrue(pas.plugins.listPluginTypeInfo())
        importPAS(ctx)
        self.assertFalse(pas.plugins.listPluginTypeInfo())

    def test_empty_adding_plugins(self):
        from Products.GenericSetup.tests.common import DummyImportContext
        from Products.GenericSetup.tests.faux_objects \
            import TestCSVAware, KNOWN_CSV
        from Products.PluggableAuthService.exportimport import importPAS

        self._setUpAdapters()
        app, pas = self._initPAS()

        ctx = DummyImportContext(pas)
        ctx._files['PAS/.objects'] = _PAS_WITH_CSV_PLUGIN_OBJECTS
        ctx._files['PAS/.properties'] = _EMPTY_PAS_PROPERTIES
        ctx._files['PAS/pluginregistry.xml'] = _EMPTY_PLUGINREGISTRY_EXPORT
        ctx._files['PAS/csv_plugin.csv'] = KNOWN_CSV

        self.assertEqual(len(pas.objectIds()), 1)
        self.assertTrue('plugins' in pas.objectIds())

        importPAS(ctx)

        self.assertEqual(len(pas.objectIds()), 2)
        self.assertTrue('plugins' in pas.objectIds())
        self.assertTrue('csv_plugin' in pas.objectIds())

        csv_plugin = pas._getOb('csv_plugin')
        self.assertTrue(csv_plugin.__class__ is TestCSVAware)
        self.assertEqual(csv_plugin._was_put.getvalue().strip(),
                         KNOWN_CSV.strip())


_EMPTY_PAS_OBJECTS = """\
plugins,plugins
"""

_PAS_WITH_CSV_PLUGIN_OBJECTS = """\
plugins,plugins
csv_plugin,Products.GenericSetup.tests.faux_objects.TestCSVAware
"""

_EMPTY_PAS_PROPERTIES = """\
[DEFAULT]
title =
"""

_EMPTY_PLUGINREGISTRY_EXPORT = """\
<?xml version="1.0"?>
<plugin-registry>
</plugin-registry>
"""


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(Test_exportPAS),
        unittest.makeSuite(Test_importPAS),
        ))
