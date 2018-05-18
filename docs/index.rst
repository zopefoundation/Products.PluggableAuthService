``Products.PluggableAuthService``
=================================

Purpose
-------
The PluggableAuthService is designed to allow incorporation of *any*
existing user folder (or related technology), and to make it
simple to define project-specific extensions.

Theory of Operation
-------------------
The PluggableAuthService defines a framework for a set of plugins which
it orchestrates to generate user objects from requests.  These user
objects implement the "traditional" BasicUser API, and provide
additional functionality.

Narrative documentation
-----------------------
Narrative documentation explaining how to use
:mod:`Products.PluggableAuthService`.

.. toctree::
   :maxdepth: 2

   plugin
   requestflow
   caching

API documentation
-----------------
API documentation for :mod:`Products.PluggableAuthService`.

.. toctree::
   :maxdepth: 2

   api/user
   api/userproperties
   api/userfolder
   api/plugins
   api/events
   api/request


Changes
-------

.. toctree::
   :maxdepth: 2

   changes


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
