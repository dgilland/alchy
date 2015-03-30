"""Generic utility functions used in package.

..
    >>> from alchy.utils import *
"""

import re
from collections import Iterable

from sqlalchemy import Column
from sqlalchemy.ext.declarative import AbstractConcreteBase

from ._compat import string_types, iteritems, itervalues, classmethod_func


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
    return (isinstance(obj, Iterable) and
            not isinstance(obj, string_types) and
            not isinstance(obj, dict))


def has_primary_key(metadict):
    """Check if meta class' dict object has a primary key defined."""
    return any(column.primary_key
               for attr, column in iteritems(metadict)
               if isinstance(column, Column))


def camelcase_to_underscore(string):
    """Convert string from ``CamelCase`` to ``under_score``."""
    return re.sub('((?<=[a-z0-9])[A-Z]|(?<!_)(?!^)[A-Z](?=[a-z]))', r'_\1',
                  string).lower()


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


def merge_declarative_args(cls, global_config_key, local_config_key):
    """Merge declarative args for class `cls`
    identified by `global_config_key` and `local_config_key`
    into a consolidated (tuple, dict).
    """
    configs = [base.__dict__.get(global_config_key)
               for base in reversed(cls.mro())]
    configs.append(cls.__dict__.get(local_config_key))

    args = []
    kargs = {}

    for obj in configs:
        if not obj:
            continue

        if isinstance(obj, classmethod):
            obj = classmethod_func(obj)(cls)
        elif callable(obj):
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


def should_set_tablename(bases, dct):
    """Check what values are set by a class and its bases to determine if a
    tablename should be automatically generated.

    The class and its bases are checked in order of precedence: the class
    itself then each base in the order they were given at class definition.

    Abstract classes do not generate a tablename, although they may have set
    or inherited a tablename elsewhere.

    If a class defines a tablename or table, a new one will not be generated.
    Otherwise, if the class defines a primary key, a new name will be
    generated.

    This supports:

    * Joined table inheritance without explicitly naming sub-models.
    * Single table inheritance.
    * Concrete table inheritance
    * Inheriting from mixins or abstract models.

    :param bases: base classes of new class
    :param dct: new class dict
    :return: True if tablename should be set
    """

    if '__tablename__' in dct or '__table__' in dct or '__abstract__' in dct:
        return False

    if has_primary_key(dct):
        return True

    if '__mapper_args__' in dct:
        is_concrete = dct.get('__mapper_args__', {}).get('concrete', False)
    else:
        is_concrete = dct.get('__global_mapper_args__', {}).get('concrete',
                                                                False)
        is_concrete = dct.get('__local_mapper_args__', {}).get('concrete',
                                                               is_concrete)

    for base in bases:
        if base is AbstractConcreteBase:
            return False

        if (not is_concrete) and (hasattr(base, '__tablename__') or
                                  hasattr(base, '__table__')):
            return False

        for name in dir(base):
            if not (name in ('query') or
                    (name.startswith('__') and name.endswith('__'))):
                attr = getattr(base, name)
                if getattr(attr, 'primary_key', False):
                    return True

    return False
