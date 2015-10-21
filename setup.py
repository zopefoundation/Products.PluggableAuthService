# -*- coding: utf-8 -*-
from setuptools import find_packages
from setuptools import setup

VERSION = '2.0.dev0'

_boundary = '\n\n'

with open('README.rst') as f:
    README = f.read()

with open('CHANGES.rst') as f:
    CHANGES = f.read()

README = (README + _boundary + CHANGES)

setup(
    name='Products.PluggableAuthService',
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
        'AccessControl >=3.0',
        'Products.GenericSetup',
        'Products.PluginRegistry',
        'setuptools',
        'zope.deprecation',
        'Zope2 >= 2.13',
    ],
    extras_require={
        'ip_range': ['IPy'],
    },
    entry_points="""
    [zope2.initialize]
    Products.PluggableAuthService = Products.PluggableAuthService:initialize
    """
)
