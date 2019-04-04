##############################################################################
#
# Copyright (c) 2001 Zope Foundation and Contributors
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this
# distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" Represent a group of properties about a user.
"""

import six

from DateTime.DateTime import DateTime
from OFS.Image import Image

from Products.PluggableAuthService.interfaces.propertysheets import \
    IPropertySheet
from Products.PluggableAuthService.utils import classImplements


StringTypes = (str, six.text_type)


def _guessSchema(kw):

    schema = []
    for k, v in kw.items():

        ptype = 'string'

        if isinstance(v, (six.binary_type, six.text_type)):
            ptype = 'string'

        elif six.PY2 and isinstance(v, long):  # noqa
            ptype = 'long'

        elif type(v) == int:
            # bool is a subsclass of int, so we cannot use isinstance
            ptype = 'int'

        elif isinstance(v, float):
            ptype = 'float'

        elif isinstance(v, bool):
            ptype = 'boolean'

        elif isinstance(v, (tuple, list)):

            if v and not isinstance(v[0], (six.binary_type, six.text_type)):
                raise ValueError('Property %s: sequence items not strings' % k)

            ptype = 'lines'

        elif isinstance(v, DateTime):
            ptype = 'date'

        elif isinstance(v, type):

            if isinstance(v, DateTime):
                ptype = 'date'
            else:
                raise ValueError('Property %s: unknown class' % k)

        elif isinstance(v, Image):
            ptype = 'image'

        elif not isinstance(v, (six.binary_type, six.text_type)):
            raise ValueError('Property %s: unknown type' % k)

        schema.append((k, ptype))

    return schema


class UserPropertySheet(object):

    """ Model a single, read-only set of properties about a user.

    o Values for the sheet are passed as keyword args to the c'tor.

    o The schema for the sheet may be passed into the c'tor explicitly
      as a sequence of (id, type) tuples;  if not passed, the c'tor will
      guess the schema from the keyword args.
    """

    def __init__(self, id, schema=None, **kw):

        self._id = id

        if schema is None:
            schema = _guessSchema(kw)

        self._schema = tuple(schema)
        self._properties = {}

        for id, ptype in schema:

            value = kw.get(id)

            if ptype == 'lines':
                if value is not None:
                    value = tuple(value)

            self._properties[id] = value

    #
    #   IPropertySheet implementation
    #
    def getId(self):

        """ See IPropertySheet.
        """
        return self._id

    def hasProperty(self, id):

        """ See IPropertySheet.
        """
        return id in self.propertyIds()

    def getProperty(self, id, default=None):

        """ See IPropertySheet.
        """
        return self._properties.get(id, default)

    def getPropertyType(self, id):

        """ See IPropertySheet.
        """
        found = [x[1] for x in self._schema if x[0] == id]

        return found and found[0] or None

    def propertyInfo(self, id):

        """ See IPropertySheet.
        """
        for schema_id, ptype in self._schema:

            if schema_id == id:
                return {'id': id, 'type': ptype, 'mode': ''}

        return None

    def propertyMap(self):

        """ See IPropertySheet.
        """
        result = []

        for id, ptype in self._schema:
            result.append({'id': id, 'type': ptype, 'mode': ''})

        return tuple(result)

    def propertyIds(self):

        """ See IPropertySheet.
        """
        return [x[0] for x in self._schema]

    def propertyValues(self):

        """ See IPropertySheet.
        """
        return [self._properties.get(x) for x in self.propertyIds()]

    def propertyItems(self):
        """ See IPropertySheet.
        """
        return [(x, self._properties.get(x)) for x in self.propertyIds()]


classImplements(UserPropertySheet, IPropertySheet)
