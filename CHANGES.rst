Change Log
==========

2.0 (unreleased)
----------------

- Support ZopeVersionControl: we need to check 'plugins' for more than
  existence, since it replaces objects (like 'plugins') with
  SimpleItems and calls _delOb, which tries to use special methods of
  'plugins'. This ports a patch of PlonePAS to the original code.
  [esteele]

- deprecations:

  - ``.utils.directlyProvides`` - use ``@provider`` from ``zope.interface``
  - ``.utils.classImplements`` - use ``@implementer`` from ``zope.interface``
  - ``.utils.postonly`` - use same from ``AccessControl.request``
  - ``.interfaces.requests.*`` - except IWebDAVRequest (missing substitute)
    use import from ``zope.publisher.interfaces.*``

  [jensens]

- Cleanup:

  - PEP8 (autopep8 + some manual refinements),
  - hashlib (Python 2.7 only),
  - depend on GenericSetup nyway, so removed conditional tests,
  - needs AccessControl >2.0 in order to use decorators,
  - remove unused imports
  - overhaul of buildout:

    - uses Zope 2.13.23,
    - added code-analysis,

  - ...

  [jensens, esteele]

- Fix usage of os.path.split(). Could result in Errors during import
  on Windows.
  [do3cc]

1.10.0 (2013-02-19)
-------------------

- Allow specifying a policy for transforming / normalizing login names
  for all plugins in a PAS:

  - Added ``login_transform`` string property to PAS.

  - Added ``applyTransform`` method to PAS, which looks for a method on PAS
    with the name specified in the ``login_transform`` property.

  - Added two possible transforms to PAS: ``lower`` and ``upper``.

  - Changed the methods of PAS to call ``applyTransform`` wherever needed.

  - Added the existing ``updateUser`` method of ZODBUserManager to the
    IUserEnumerationPlugin interface.

  - Added a new ``updateEveryLoginName`` method to ZODBUserManager and the
    IUserEnumerationPlugin interface.

  - Added three methods to PAS and IPluggableAuthService:
    ``updateLoginName``, ``updateOwnLoginName``, ``updateAllLoginNames``.
    These methods call ``updateUser`` or ``updateEveryLoginName`` on every
    IUserEnumerationPlugin. Since these are later additions to the plugin
    interface, we log a warning when a plugin does not have these methods
    (for example the ``mutable_properties`` plugin of PlonePAS) but will
    not fail.  When no plugin is able to update a user, this will raise an
    exception: we do not want to quietly let this pass when for example a
    login name is already taken by another user.

  - Changing the ``login_transform`` property in the ZMI will call
    ``PAS.updateAllLoginNames``, unless ``login_transform`` is the same or
    has become an empty string.

  - The new ``login_transform`` property is empty by default. In that case,
    the behavior of PAS is the same as previously. The various
    ``applyTransform`` calls will have a (presumably very small)
    performance impact.

- Launchpad #1079204:  Added CSRF protection for the ZODBUserManager,
  ZODBGroupManager, ZODBRoleManger, and DynamicGroupsPlugin plugins.


1.9.0 (2012-08-30)
------------------

- Launchpad #649596:  add a protocol for plugins which check whether a
  non-top-level PAS instance is "competent" to authenticate a given request;
  if not, the instance defers to higher-level instances.  Thanks to Dieter
  Maurer for the patch.


1.8.0 (2012-05-08)
------------------

- Added export / import support for the ChallengeProtocolChooser plugin's
  label - protocols mapping.


1.7.8 (2012-05-08)
------------------

- In authenticateCredentials do NOT fall back to using the login as
  userid when there is no match, as that gives a high chance of
  seeming to log in successfully, but in reality failing.
  [maurits]


1.7.7 (2012-02-27)
------------------

- Explicitly encode/decode data for GS


1.7.6 (2011-10-31)
------------------

- Launchpad #795086:  fixed creation of PropertiesUpdated event.


1.7.5 (2011-05-30)
------------------

- Launchpad #789858:  don't allow conflicting login name in 'updateUser'.

- Set appropriate cache headers on CookieAuthHelper login redirects to prevent
  caching by proxy servers.


1.7.4 (2011-05-13)
------------------

- Added forward compatibility with DateTime 3.


1.7.3 (2011-02-10)
------------------

- In the ZODBRoleManager made it clearer that adding a removing a role
  does not have much effect if you do not do the same in the root of
  the site (at the bottom of the Security tab at manage_access).
  Fixes https://bugs.launchpad.net/zope-pas/+bug/672694

- Return the created user in _doAddUser, to match change in
  AccessControl 2.13.4.

- Fixed possible ``binascii.Error`` in ``extractCredentials`` of
  CookieAuthHelper. This is a corner case that might happen after
  a browser upgrade.


1.7.2 (2010-11-11)
------------------

- Allow for a query string in CookieAuthHelper's ``login_path``.

- Trap "swallowable" exceptions from ``IRoles`` plugins.  Thanks to
  Willi Langenburger for the patch.  Fixes
  https://bugs.launchpad.net/zope-pas/+bug/615474 .

- Fixed possible TypeError in ``extractCredentials`` of CookieAuthHelper
  when the ``__ac`` cookie is not ours (but e.g. from plone.session,
  though even then only in a corner case).

- Fixed chameleon incompatibilities


1.7.1 (2010-07-01)
------------------

- Made ``ZODBRoleManager.assignRoleToPrincipal`` raise and log a more
  informative error when detecting a duplicate principal.
  https://bugs.launchpad.net/zope-pas/+bug/348795

- Updated ``DynamicGroupsPlugin.enumerateGroups`` to return an empty sequence
  for an unknown group ID, rather than raising KeyError.
  https://bugs.launchpad.net/zope-pas/+bug/585365

- Updated all code to raise new-style exceptions.

- Removed dependency on ``zope.app.testing``.

- Cleaned out a number of old imports, because we now require Zope >= 2.12.

- Updated ``setDefaultRoles`` to use the ``addPermission`` API if available.


1.7.0 (2010-04-08)
------------------

- Allow CookieAuthHelper's ``login_path`` to be set to an absolute url for
  integration with external authentication mechanisms.

- Fixed xml templates directory path computation to allow reuse of
  ``SimpleXMLExportImport`` class outside ``Products.PluggableAuthService``.


1.7.0b2 (2010-01-31)
--------------------

- Modify ZODBGroupManager to update group title and description independently.


1.7.0b1 (2009-11-16)
--------------------

- This release requires for Zope2 >= 2.12.

- Simplified buildout to just what is needed to run tests.

- Don't fail on users defined in multiple user sources on the
  ZODBGroupManager listing page.

- Fixed deprecation warnings for use of ``Globals`` under Zope 2.12.

- Fixed deprecation warnings for the ``md5`` and ``sha`` modules under
  Python >= 2.6.


1.6.2 (2009-11-16)
------------------

- Launchpad #420319:  Fix misconfigured ``startswith`` match type filter
  in ``Products.PluggableAuthService.plugins.DomainAuthHelper``.

- Fixed test setup for tests using page templates relying on the
  ``DefaultTraversable`` adapter.

- Fixed broken markup in templates.


1.6.1 (2008-11-20)
------------------

- Launchpad #273680:  Avoid expensive / incorrect dive into ``enumerateUsers``
  when trying to validate w/o either a real ID or login.

- Launchpad #300321:
  ``Products.PluggableAuthService.pluginsZODBGroupManager.enumerateGroups``
  failed to find groups with unicode IDs.


1.6 (2008-08-05)
----------------

- Fixed another deprecation for ``manage_afterAdd`` occurring when used
  together with Five (this time for the ``ZODBRoleManager`` class).

- Ensure the ``_findUser`` cache is invalidated if the roles or groups for
  a principal change.

- Launchpad #15569586:  docstring fix.

- Factored out ``filter`` logic into separate classes;  added filters
  for ``startswith`` test and (if the IPy module is present) IP-range
  tests.  See https://bugs.launchpad.net/zope-pas/+bug/173580 .

- Zope 2.12 compatibility - removed ``Interface.Implements`` import if
  ``zope.interface`` available.

- Ensure ``ZODBRoleManagerExportImport`` doesn't fail if it tries to add a
  role that already exists (idempotence is desirable in GS importers)

- Fixed tests so they run with Zope 2.11.

- Split up large permission tests into individual tests.

- Fixed deprecation warning occurring when used together with
  Five. (``manage_afterAdd`` got undeprecated.)

- Added buildout.


1.5.3 (2008-02-06)
------------------

- ZODBUserManager plugin: allow unicode arguments to
  ``enumerateUsers``. (https://bugs.launchpad.net/zope-pas/+bug/189627)

- plugins/ZODBRoleManager: added logging in case searchPrincipial()
  returning more than one result (which might happen in case of having
  duplicate id within difference user sources)


1.5.2 (2007-11-28)
------------------

- DomainAuthHelper plugin:  fix glitch for plugins which have never
  configured any "default" policy:  ``authenticateCredentials`` and
  ``getRolesForPrincipal`` would raise ValueError.
  (http://www.zope.org/Collectors/PAS/59)


1.5.1 (2007-09-11)
------------------

- PluggableAuthService._verifyUser: changed to use exact_match to the
  enumerator, otherwise a user with login ``foobar`` might get returned
  by _verifyUser for a query for ``login='foo'`` because the enumerator
  happened to return 'foobar' first in the results.

- Add a test for manage_zmi_logout and replace a call to isImplementedBy
  with providedBy.
  (http://www.zope.org/Collectors/PAS/58)


1.5 (2006-06-17)
----------------

- Add support for property plugins returning an IPropertySheet
  to PropertiedUser. Added addPropertysheet to the IPropertiedUser.

- Added a method to the IRoleAssignerPlugin to remove roles from a
  principal, and an implementation for it on the ZODBRoleManager.
  (http://www.zope.org/Collectors/PAS/57)

- Added events infrastructure. Enabled new IPrincipalCreatedEvent and
  ICredentialsUpdatedEvent events.

- Added support for registering plugin types via ZCML.

- Implemented authentication caching in _extractUserIds.

- Ported standard user folder tests from the AccessControl test suite.

- Passwords with ":" characters would break authentication
  (http://www.zope.org/Collectors/PAS/51)

- Corrected documented software dependencies

- Converted to publishable security sensitive methods to only accept
  POST requests to prevent XSS attacks.  See
  http://www.zope.org/Products/Zope/Hotfix-2007-03-20/announcement and
  http://dev.plone.org/plone/ticket/6310

- Fixed issue in the user search filter where unrecognized keyword
  arguments were ignored resulting in duplicate search entries.
  (http://dev.plone.org/plone/ticket/6300)

- Made sure the Extensions.upgrade script does not commit full
  transactions but only sets (optimistic) savepoints. Removed bogus
  Zope 2.7 compatibility in the process.
  (http://www.zope.org/Collectors/PAS/55)

- Made the CookieAuthHelper only use the ``__ac_name`` field if
  ``__ac_password`` is also present. This fixes a login problem for
  CMF sites where the login name was remembered between sessions with
  an ``__ac_name`` cookie.

- Made the DomainAuthHelper return the remote address, even it the
  remote host is not available (http://www.zope.org/Collectors/PAS/49).

- Fixed bug in DelegatingMultiPlugin which attempted to validate the
  supplied password directly against the user password - updated to use
  AuthEncoding.pw_validate to handle encoding issues

- Fixed serious security hole in DelegatingMultiPlugin which allowed
  Authentication if the EmergencyUser login was passed in.  Added
  password validation utilizing AuthEncoding.pw_validate

- Fixed a set of tests that tested values computed from dictionaries
  and could break since dictionaries are not guaranteed to have any
  sort order.

- Fixed test breakage induced by use of Z3 pagetemplates in Zope
  2.10+.

- BasePlugin: The listInterfaces method only considered the old-style
  __implements__ machinery when determining interfaces provided by
  a plugin instance.

- ZODBUserManager: Already encrypted passwords were encrypted again in
  addUser and updateUserPassword.
  (http://www.zope.org/Collectors/Zope/1926)

- Made sure the emergency user via HTTP basic auth always wins, no matter
  how borken the plugin landscape.

- Cleaned up code in CookieAuthHelper which allowed the form to override
  login/password if a cookie had already been set.

- Removed some BBB code for Zope versions < 2.8, which is not needed
  since we require Zope > 2.8.5 nowadays.

