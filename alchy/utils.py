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
    return (re.sub('((?<=[a-z0-9])[A-Z]|(?!^)[A-Z](?=[a-z]))', r'_\1', string)
            .lower())


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


def iterunique(items):
    """Return iterator to find unique list while preserving the order."""
    seen = []
    for item in items:
        if item not in seen:
            seen.append(item)
            yield item


def unique(items):
    """Return unique list while preserving the order.

    >>> assert unique([1, 2, 3, 1, 2, 3, 4]) == [1, 2, 3, 4]
    """
    return list(iterunique(items))


def mapper_class(relation):
    """Return mapper class given an ORM relation attribute."""
    return relation.property.mapper.class_


def get_mapper_class(model, field):
    """Return mapper class given ORM model and field string."""
    return mapper_class(getattr(model, field))


def merge_declarative_args(base_classes, config_key):
    """Given a list of base classes, merge declarative args identified by
    `config_key` into a single configuration object.
    """
    configs = [getattr(base, config_key, None)
               for base in reversed(base_classes)]
    args = []
    kargs = {}

    for obj in configs:
        if not obj:
            continue

        if callable(obj):
            obj = obj()

        if isinstance(obj, dict):
            kargs.update(obj)
        elif isinstance(obj[-1], dict):
            # Configuration object has a dict at the end so we assume the
            # passed in format was [item0, item1, ..., dict0].
            args += obj[:-1]
            kargs.update(obj[-1])
        else:
            args += obj

    # Make args unique in case base classes duplicated items.
    args = unique(args)

    return (args, kargs)
