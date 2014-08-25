"""Collection of custom column types.
"""

import re

from sqlalchemy.types import SchemaType, TypeDecorator, Enum

from ._compat import with_metaclass


__all__ = [
    'DeclarativeEnumType',
    'DeclarativeEnum'
]


##
# Declarative Enum type
# Adapted from the Enum Recipe:
# http://techspot.zzzeek.org/2011/01/14/the-enum-recipe/
##

class EnumSymbol(object):
    """Define a fixed symbol tied to a parent class."""

    def __init__(self, enum_class, name, value, description):
        self.enum_class = enum_class
        self.name = name
        self.value = value
        self.description = description

    def __reduce__(self):
        """Allow unpickling to return the symbol linked to the DeclarativeEnum
        class.
        """
        return getattr, (self.enum_class, self.name)

    def __iter__(self):
        return iter([self.value, self.description])

    def __repr__(self):
        return "<%s>" % self.name

    def __str__(self):
        return self.name

    def to_dict(self):
        """Represent symbol as dict."""
        return {'value': self.value, 'description': self.description}


class EnumMeta(type):
    """Generate new DeclarativeEnum classes."""

    def __init__(cls, classname, bases, dct):
        cls._reg = cls._reg.copy()
        for name, value in dct.items():
            if isinstance(value, tuple):
                sym = cls._reg[value[0]] = EnumSymbol(cls, name, *value)
                setattr(cls, name, sym)
        type.__init__(cls, classname, bases, dct)

    def __iter__(cls):
        return iter(cls._reg.values())


class DeclarativeEnumType(SchemaType, TypeDecorator):
    """Column type usable in table column definitions."""

    def __init__(self, enum):
        self.enum = enum
        constraint = 'ck{0}'.format(re.sub('([A-Z])',
                                           lambda m: '_' + m.group(1).lower(),
                                           enum.__name__))
        self.impl = Enum(*enum.values(), name=constraint)

    def _set_table(self, table, column):
        self.impl._set_table(table, column)

    def copy(self):
        return DeclarativeEnumType(self.enum)

    def process_bind_param(self, value, dialect):
        if value is None:  # pragma: no cover
            return None
        return value.value

    def process_result_value(self, value, dialect):
        if value is None:  # pragma: no cover
            return None
        return self.enum.from_string(value.strip())


class DeclarativeEnum(with_metaclass(EnumMeta, object)):
    """Declarative enumeration.

    For example::

        class OrderStatus(DeclarativeEnum):
            pending = ('p', 'Pending')
            submitted = ('s', 'Submitted')
            complete = ('c', 'Complete')

        class Order(Model):
            status = Column(OrderStatus.db_type(), default=OrderStatus.pending)
    """

    _reg = {}

    @classmethod
    def from_string(cls, string):
        """Return enum symbol given string value.

        Raises:
            ValueError: If `string` doesn't correspond to an enum value.
        """
        try:
            return cls._reg[string]
        except KeyError:
            raise ValueError('Invalid value for %r: %r' % (cls.__name__,
                                                           string))

    @classmethod
    def values(cls):
        """Return list of possible enum values. Each value is a valid argument
        to :meth:`from_string`.
        """
        return cls._reg.keys()

    @classmethod
    def db_type(cls):
        """Return database column type for use in table column definitions."""
        return DeclarativeEnumType(cls)
