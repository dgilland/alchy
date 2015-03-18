# pylint: skip-file
"""Python 2/3 compatibility

    Some py2/py3 compatibility support based on a stripped down
    version of six so we don't have to depend on a specific version
    of it.

    Borrowed from
    https://github.com/mitsuhiko/flask/blob/master/flask/_compat.py
"""

import sys


PY3 = sys.version_info[0] == 3


def _identity(x): return x


if PY3:
    text_type = str
    string_types = (str,)
    integer_types = (int,)

    def iterkeys(d): return iter(d.keys())

    def itervalues(d): return iter(d.values())

    def iteritems(d): return iter(d.items())

    from io import StringIO

    def reraise(tp, value, tb=None):
        if value.__traceback__ is not tb:
            raise value.with_traceback(tb)
        raise value

    implements_to_string = _identity
else:
    text_type = unicode
    string_types = (str, unicode)
    integer_types = (int, long)

    def iterkeys(d): return d.iterkeys()

    def itervalues(d): return d.itervalues()

    def iteritems(d): return d.iteritems()

    from cStringIO import StringIO

    exec('def reraise(tp, value, tb=None):\n raise tp, value, tb')

    def implements_to_string(cls):
        cls.__unicode__ = cls.__str__
        cls.__str__ = lambda x: x.__unicode__().encode('utf-8')
        return cls


def with_metaclass(meta, *bases):
    # This requires a bit of explanation: the basic idea is to make a
    # dummy metaclass for one level of class instantiation that replaces
    # itself with the actual metaclass.  Because of internal type checks
    # we also need to make sure that we downgrade the custom metaclass
    # for one level to something closer to type (that's why __call__ and
    # __init__ comes back from type etc.).
    #
    # This has the advantage over six.with_metaclass in that it does not
    # introduce dummy classes into the final MRO.
    class metaclass(meta):
        __call__ = type.__call__
        __init__ = type.__init__

        def __new__(cls, name, this_bases, d):
            if this_bases is None:
                return type.__new__(cls, name, (), d)
            return meta(name, bases, d)
    return metaclass('temporary_class', None, {})


# Certain versions of pypy have a bug where clearing the exception stack
# breaks the __exit__ function in a very peculiar way.  This is currently
# true for pypy 2.2.1 for instance.  The second level of exception blocks
# is necessary because pypy seems to forget to check if an exception
# happend until the next bytecode instruction?
BROKEN_PYPY_CTXMGR_EXIT = False
if hasattr(sys, 'pypy_version_info'):
    class _Mgr(object):
        def __enter__(self):
            return self

        def __exit__(self, *args):
            sys.exc_clear()
    try:
        try:
            with _Mgr():
                raise AssertionError()
        except:
            raise
    except TypeError:
        BROKEN_PYPY_CTXMGR_EXIT = True
    except AssertionError:
        pass


# Define classmethod_func(f) to retrieve the unbound function of classmethod f
if sys.version_info[:2] >= (2, 7):
    def classmethod_func(f): return f.__func__
else:
    def classmethod_func(f): return f.__get__(1).im_func
