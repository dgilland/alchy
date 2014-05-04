"""Generic utility functions used in package.
"""

import re
from collections import Iterable

from sqlalchemy import Column, and_

from ._compat import string_types, iteritems


class classproperty(object):
    """Decorator that adds class properties. Allows for usage like @property
    but applies the property at the class level. Helps avoid having to use
    metaclasses or other complex techniques to achieve similar results.
    """
    def __init__(self, getter):
        self.getter = getter

    def __get__(self, instance, owner):
        return self.getter(owner)


def is_sequence(obj):
    """Test if `obj` is an iterable but not dict or string. Mainly used to
    determine if `obj` can be treated like a list for iteration purposes.
    """
    return (isinstance(obj, Iterable)
            and not isinstance(obj, string_types)
            and not isinstance(obj, dict))


def has_primary_key(metadict):
    """Check if meta class' dict object has a primary key defined."""
    return any(column.primary_key
               for attr, column in iteritems(metadict)
               if isinstance(column, Column))


def base_columns_from_subquery(subquery):
    """Return non-aliased, base columns from subquery."""
    # base_columns is a set so we need to cast to list.
    return [(column, list(column.base_columns))
            for column in subquery.c.values()]


def join_subquery_on_columns(subquery, columns):
    """Return join-on condition which maps subquery's columns to columns."""
    subquery_base_columns = base_columns_from_subquery(subquery)

    join_on = []
    for subquery_column, base_columns in subquery_base_columns:
        # Don't support joining to subquery column with more than 1 base
        # column.
        if len(base_columns) == 1 and base_columns[0] in columns:
            join_on.append(subquery_column == base_columns[0])

    if join_on:
        return and_(*join_on)
    else:  # pragma: no cover
        return None


def camelcase_to_underscore(string):
    """Convert string from CamelCase to under_score"""
    regex_first_cap = re.compile('(.)([A-Z][a-z]+)')
    regex_all_cap = re.compile('([a-z0-9])([A-Z])')

    first_cap = regex_first_cap.sub(r'\1_\2', string)
    return regex_all_cap.sub(r'\1_\2', first_cap).lower()


def iterflatten(items):
    """Return iterator which flattens list/tuple of lists/tuples
    >>> to_flatten = [1, [2,3], [4, [5, [6]], 7], 8]
    >>> assert list(iterflatten(to_flatten)) == [1,2,3,4,5,6,7,8]
    """
    for item in items:
        if isinstance(item, (list, tuple)):
            for itm in flatten(item):
                yield itm
        else:
            yield item


def flatten(items):
    """Return flattened list of a list/tuple of lists/tuples
    >>> assert flatten([1, [2,3], [4, [5, [6]], 7], 8]) == [1,2,3,4,5,6,7,8]
    """
    return list(iterflatten(items))
