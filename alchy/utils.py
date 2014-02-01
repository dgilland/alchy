
from collections import Iterable

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
    '''
    Test if `obj` is an iterable but not dict or string
    '''
    return isinstance(obj, Iterable) and not isinstance(obj, basestring) and not isinstance(obj, dict)
