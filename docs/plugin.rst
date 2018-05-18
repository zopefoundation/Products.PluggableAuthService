Plugins
=======

Plugin Types
------------
PluggableAuthService defines the following plugin types:

  - Authentication plugins identify the user based on data in the request.
    
    o Each PluggableAuthService must contain at least one authentication
      plugin.

    o The PluggableAuthService defines an ordered set of authentication
      plugins, and queries them in order for each request.  The first plugin
      to recognize a user returns the user, or raises an exception
      (e.g., for password mismatches).  If no plugin returns a user,
      the PluggableAuthService returns an "anonymous" user (which may still
      have "extended" information added later).

  - Challenge plugins alter the response to force the user to
    (re)authenticate, e.g. by redirecting it to a
    login form, or by setting the protocol-specific headers which
    initiate the desired challenge.

  - Decorator plugins add propertysheets to a user, based on request
    data or on other data sources.

    o These sources might include application data from the ZODB or
      from SQL, etc.

    o They might also pull in user data from LDAP, ActiveDirectory,
      passwd files, etc.

  - Group plugins add groups to the list of groups to which the user
    belongs, using request data or previously-added decorations.

  - Update plugins write updates back to the data store from which
    they came (ZODB, SQL, LDAP, etc.)

  - Validation plugins impose business-specified policies on user
    properties (particularly on login ID and password).


Plugin Registration
-------------------
PluggableAuthService plugins are configured via the ZMI, or alternatively
via an XML import / export mechanism.  Each plugin is identified
using a TALES path expression, which will be evaluated with an
implied 'nocall' modifier;  plugins are intended to be callables,
with known argument signatures.
