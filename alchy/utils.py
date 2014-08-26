"""Generic utility functions used in package.

..
    >>> from alchy.utils import *
"""

import re
from collections import Iterable

from sqlalchemy import Column

from ._compat import string_types, iteritems


__all__ = [
    'is_sequence',
    'has_primary_key',
    'camelcase_to_underscore',
    'iterflatten',
    'flatten'
]


def is_sequence(obj):
    """Test if `obj` is an iterable but not ``dict`` or ``str``. Mainly used to
    determine if `obj` can be treated like a ``list`` for iteration purposes.
    """
    return (isinstance(obj, Iterable)
            and not isinstance(obj, string_types)
            and not isinstance(obj, dict))


def has_primary_key(metadict):
    """Check if meta class' dict object has a primary key defined."""
    return any(column.primary_key
               for attr, column in iteritems(metadict)
               if isinstance(column, Column))


def camelcase_to_underscore(string):
    """Convert string from ``CamelCase`` to ``under_score``."""
    regex_first_cap = re.compile('(.)([A-Z][a-z]+)')
    regex_all_cap = re.compile('([a-z0-9])([A-Z])')

    first_cap = regex_first_cap.sub(r'\1_\2', string)
    return regex_all_cap.sub(r'\1_\2', first_cap).lower()


def iterflatten(items):
    """Return iterator which flattens list/tuple of lists/tuples::

    >>> to_flatten = [1, [2,3], [4, [5, [6]], 7], 8]
    >>> assert list(iterflatten(to_flatten)) == [1,2,3,4,5,6,7,8]
    """
    for item in items:
        if isinstance(item, (list, tuple)):
            for itm in iterflatten(item):
                yield itm
        else:
            yield item


def flatten(items):
    """Return flattened list of a list/tuple of lists/tuples::

    >>> assert flatten([1, [2,3], [4, [5, [6]], 7], 8]) == [1,2,3,4,5,6,7,8]
    """
    return list(iterflatten(items))
