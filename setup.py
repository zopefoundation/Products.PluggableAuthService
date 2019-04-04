import os

from setuptools import find_packages
from setuptools import setup


NAME = 'PluggableAuthService'

here = os.path.abspath(os.path.dirname(__file__))


def _package_doc(name):
    f = open(os.path.join(here, name))
    return f.read()


_boundary = '\n\n'

with open('README.rst') as f:
    README = f.read()

with open('CHANGES.rst') as f:
    CHANGES = f.read()

README = (README + _boundary + CHANGES)

setup(name='Products.%s' % NAME,
      version=_package_doc('version.txt').strip(),
      description='Pluggable Zope authentication / authorization framework',
      long_description=README,
      classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Framework :: Plone',
        'Framework :: Zope :: 4',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Zope Public License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Software Development',
        'Topic :: System :: Systems Administration :: '
        'Authentication/Directory',
        ],
      keywords='web application server zope',
      author='Zope Foundation and Contributors',
      author_email='zope-cmf@zope.org',
      url='https://productspluggableauthservice.readthedocs.io',
      project_urls={
          'Documentation': ('https://productspluggableauthservice.'
                            'readthedocs.io'),
          'Issue Tracker': ('https://github.com/zopefoundation'
                            '/Products.PluggableAuthService/issues'),
          'Sources': ('https://github.com/zopefoundation/'
                      'Products.PluggableAuthService'),
      },
      license='ZPL 2.1 (http://www.zope.org/Resources/License/ZPL-2.1)',
      packages=find_packages(),
      include_package_data=True,
      namespace_packages=['Products'],
      zip_safe=False,
      python_requires='>=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*,!=3.4.*',
      install_requires=[
          'setuptools',
          'six',
          'Zope >= 4.0b6',
          'AccessControl >= 4.0a1',
          'Products.PluginRegistry >= 1.6',
          'Products.GenericSetup >= 2.0b1',
          'Products.StandardCacheManagers',
          ],
      extras_require={
          'ip_range': ['IPy'],
          'zserver': ['ZServer >= 4.0a1'],
          'docs': ['Sphinx', 'repoze.sphinx.autointerface'],
      },
      entry_points="""
      [zope2.initialize]
      Products.%s = Products.%s:initialize
      """ % (NAME, NAME),
      )
