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
README = ( open('README.txt').read()
         + _boundary
         + open('CHANGES.txt').read()
         )

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
          'Products.PluginRegistry',
          'Products.GenericSetup',
          'Zope2 >= 2.12',
          ],
      extras_require={'ip_range': ['IPy'],
                     },
      entry_points="""
      [zope2.initialize]
      Products.%s = Products.%s:initialize
      """ % (NAME, NAME),
      )
