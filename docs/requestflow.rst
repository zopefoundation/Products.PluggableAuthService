Request flow
============

1. The publisher asks the PluggableAuthService to validate the user's access
   to a given object::

    groups.validate( request, auth, roles )

2. PluggableAuthService polls its authentication plugins in order, asking
   each in turn for a user::

    for id, plugin in self.listAuthenticationPlugins():

        try:
            user = plugin( request, auth )

        except Unauthorized:
            self.dispatchChallenge( request )

        else:
            user.setAuthenticationSource( id )
            break
        
    else:
        user = self.createAnonymousUser()

3. PluggableAuthService allows each of its decorator plugins to annotate
   the user::

    for id, plugin in self.listDecoratorPlugins():

        known, schema, data = plugin( user )

        if known:
            sheet = UserPropertySheet( id, schema, **data )
            user.addPropertySheet( id, sheet )

4. PluggableAuthService allows each of its group plugins to assert groups
   for the user::

    for id, plugin in self.listGroupPlugins():

        groups = plugin( user )
        user.addGroups( groups )

5. PluggableAuthService returns the annotated / group-ified user to the
   publisher.
