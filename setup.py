import os
from setuptools import setup
from setuptools import find_packages

NAME = 'PluggableAuthService'

here = os.path.abspath(os.path.dirname(__file__))
package = os.path.join(here, 'Products', NAME)

def _package_doc(name):
    f = open(os.path.join(package, name))
    return f.read()

_boundary = '\n\n'

with open('README.rst') as f:
    README = f.read()

with open('CHANGES.rst') as f:
    CHANGES = f.read()

README = ( README + _boundary + CHANGES)

setup(name='Products.%s' % NAME,
      version=_package_doc('version.txt').strip(),
      description='Pluggable Zope2 authentication / authorization framework',
      long_description=README,
      classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Framework :: Plone",
        "Framework :: Zope2",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Zope Public License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Topic :: Software Development",
        "Topic :: System :: Systems Administration :: "
                "Authentication/Directory",
        ],
      keywords='web application server zope zope2',
      author="Zope Foundation and Contributors",
      author_email="zope-cmf@zope.org",
      url="http://pypi.python.org/pypi/Products.PluggableAuthService",
      license="ZPL 2.1 (http://www.zope.org/Resources/License/ZPL-2.1)",
      packages=find_packages(),
      include_package_data=True,
      namespace_packages=['Products'],
      zip_safe=False,
      install_requires=[
          'setuptools',
          'Zope2 >= 4.0a3',
          'Products.PluginRegistry >= 1.5',
          'Products.GenericSetup >= 1.9.0',
          'Products.StandardCacheManagers',
          'ZServer',
          ],
      extras_require={'ip_range': ['IPy'],
                     },
      entry_points="""
      [zope2.initialize]
      Products.%s = Products.%s:initialize
      """ % (NAME, NAME),
      )
