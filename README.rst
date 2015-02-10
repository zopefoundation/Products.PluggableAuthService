Products.PluggableAuthService README
====================================

This product defines a fully-pluggable user folder, intended for
use in all Zope2 sites.

Installation
------------

The normal way it install this package is via ``setuptools``, either
via ``easy_install`` into a virtual environment::

  $ cd /path/to/virtualenv
  $ bin/easy_install Products.PluggableAuthService

or by including the package in the configuration for a ``zc.buildout``-based
deployment::

  $ cd /path/to/buildout
  $ grep "eggs =" buildout.cfg
  ...
  eggs = Products.PluggableAuthService
  ...

The product can also be installed as a depencency of another distribution.

If you want to install this package manually, without using setuptools,
simply untar the package file downloaded from the PyPI site and look for
the folder named "PluggableAuthService" underneath the "Products" folder 
at the root of the extracted tarball. Copy or link this 
"PluggableAuthService" folder into your Zope "Products" folder and restart 
Zope.


Documentation
-------------

Please see the files under doc/ in the packaged software for more
information, and consult the interfaces files under interfaces/ in
the software package for PluggableAuthService and plugin APIs.

