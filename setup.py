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

setup(
    name='Products.%s' % NAME,
    version=_package_doc('version.txt').strip(),
    description='Pluggable Zope authentication / authorization framework',
    long_description=README,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Framework :: Plone',
        'Framework :: Zope :: 5',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Zope Public License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Topic :: Software Development',
        'Topic :: System :: Systems Administration'
        ' :: Authentication/Directory',
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
    license='ZPL-2.1 (http://www.zope.org/Resources/License/ZPL-2.1)',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    namespace_packages=['Products'],
    zip_safe=False,
    python_requires='>=3.9',
    install_requires=[
        'setuptools',
        'Zope >= 5',
        'AccessControl >= 4.0a1',
        'Products.PluginRegistry >= 1.6',
        'Products.GenericSetup >= 2.1.2',
        'Products.Sessions',
        'Products.StandardCacheManagers',
    ],
    extras_require={
        'ip_range': ['IPy'],
        'docs': ['Sphinx', 'repoze.sphinx.autointerface'],
    },
    entry_points="""
    [zope2.initialize]
    Products.{} = Products.{}:initialize
    """.format(NAME, NAME),
)
