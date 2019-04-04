Products.PluggableAuthService
=============================

.. image:: https://api.travis-ci.org/zopefoundation/Products.PluggableAuthService.svg?branch=master
   :target: https://travis-ci.org/zopefoundation/Products.PluggableAuthService

.. image:: https://coveralls.io/repos/github/zopefoundation/Products.PluggableAuthService/badge.svg
   :target: https://coveralls.io/github/zopefoundation/Products.PluggableAuthService

.. image:: https://readthedocs.org/projects/productspluggableauthservice/badge/?version=latest
   :target: https://productspluggableauthservice.readthedocs.io/
   :alt: Documentation Status

.. image:: https://img.shields.io/pypi/v/Products.PluggableAuthService.svg
   :target: https://pypi.org/project/Products.PluggableAuthService/
   :alt: Latest stable release on PyPI

.. image:: https://img.shields.io/pypi/pyversions/Products.PluggableAuthService.svg
   :target: https://pypi.org/project/Products.PluggableAuthService/
   :alt: Stable release supported Python versions`

This product defines a fully-pluggable user folder, intended for
use in all Zope sites.

Installation
------------

The normal way it install this package is via ``setuptools``, either
via ``pip`` into a virtual environment::

  $ cd /path/to/virtualenv
  $ bin/pip install Products.PluggableAuthService

or by including the package in the configuration for a ``zc.buildout``-based
deployment::

  $ cd /path/to/buildout
  $ grep "eggs =" buildout.cfg
  ...
  eggs = Products.PluggableAuthService
  ...

The product can also be installed as a dependency of another distribution.

Documentation
-------------

Please see the files under `doc/` in the packaged software for more
information, and consult the interfaces files under `interfaces/` in
the software package for PluggableAuthService and plugin APIs.

The documentation is also online available at https://productspluggableauthservice.readthedocs.io/.

