
import re
from collections import Iterable

from sqlalchemy import Column
import six


class classproperty(object):
    '''
    Decorator that adds class properties.
    Allows for usage like @property but applies the property at the class level.
    Helps avoid having to use metaclasses or other complex techniques to achieve similar results.
    '''
    def __init__(self, getter):
        self.getter = getter

    def __get__(self, instance, owner):
        return self.getter(owner)


def is_sequence(obj):
    '''Test if `obj` is an iterable but not dict or string'''
    return isinstance(obj, Iterable) and not isinstance(obj, six.string_types) and not isinstance(obj, dict)


def has_primary_key(obj):
    return any(v.primary_key for k, v in six.iteritems(obj) if isinstance(v, Column))


first_cap_re = re.compile('(.)([A-Z][a-z]+)')
all_cap_re = re.compile('([a-z0-9])([A-Z])')


def camelcase_to_underscore(name):
    s1 = first_cap_re.sub(r'\1_\2', name)
    return all_cap_re.sub(r'\1_\2', s1).lower()
