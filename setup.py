import os
from setuptools import setup
from setuptools import find_packages

here = os.path.abspath(os.path.dirname(__file__))
package = os.path.join(here, 'Products', 'PluggableAuthService')

def _package_doc(name):
    f = open(os.path.join(package, name))
    return f.read()

NAME = 'PluggableAuthService'

VERSION = _package_doc('version.txt').strip()
if VERSION.startswith(NAME):
    VERSION = VERSION[len(NAME):]
while VERSION and VERSION[0] in '-_.':
    VERSION = VERSION[1:]

_boundary = '\n' + ('-' * 60) + '\n'
README = ( _package_doc('README.txt')
         + _boundary + _package_doc('doc/CHANGES.txt')
         + _boundary + "\nDownload\n========"
         )

setup(name='Products.PluggableAuthService',
      version=VERSION,
      description='Pluggable Zope2 authentication / authorization framework',
      long_description=README,
      classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Framework :: Plone",
        "Framework :: Zope2",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Zope Public License",
        "Programming Language :: Python",
        "Topic :: Software Development",
        "Topic :: Security",
        "Topic :: System :: Systems Administration :: "
                "Authentication/Directory",
        ],
      keywords='web application server zope zope2',
      author="Zope Corporation and contributors",
      author_email="zope-cmf@lists.zope.org",
      url="http://pypi.python.org/pypi/Products.PluggableAuthService",
      license="ZPL 2.1 (http://www.zope.org/Resources/License/ZPL-2.1)",
      packages=find_packages(),
      include_package_data=True,
      namespace_packages=['Products'],
      zip_safe=False,
      install_requires=[
                'setuptools',
                'Products.PluginRegistry >= 1.1',
                ],
      extras_require={'exportimport': ['Products.GenericSetup >= 1.3'],
                     },
      entry_points="""
      [zope2.initialize]
      Products.PluggableAuthService = Products.PluggableAuthService:initialize
      """,
      )
