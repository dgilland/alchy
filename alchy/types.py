"""Custom ORM column types.
"""

import re

from sqlalchemy.types import SchemaType, TypeDecorator, Enum

from ._compat import with_metaclass


##
# Declarative Enum type
# Adapted from the Enum Recipe:
# http://techspot.zzzeek.org/2011/01/14/the-enum-recipe/
##

class EnumSymbol(object):
    """Define a fixed symbol tied to a parent class."""

    def __init__(self, cls_, name, value, description):
        self.cls_ = cls_
        self.name = name
        self.value = value
        self.description = description

    def __reduce__(self):
        """Allow unpickling to return the symbol linked to the DeclarativeEnum
        class.
        """
        return getattr, (self.cls_, self.name)

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

    def __init__(cls, classname, bases, dict_):
        cls._reg = reg = cls._reg.copy()
        for k, v in dict_.items():
            if isinstance(v, tuple):
                sym = reg[v[0]] = EnumSymbol(cls, k, *v)
                setattr(cls, k, sym)
        type.__init__(cls, classname, bases, dict_)

    def __iter__(cls):
        return iter(cls._reg.values())


class DeclarativeEnumType(SchemaType, TypeDecorator):
    """Column type usable in table column definitions."""

    def __init__(self, enum):
        self.enum = enum
        self.impl = Enum(
            *enum.values(),
            name="ck%s" % re.sub('([A-Z])',
                                 lambda m: "_" + m.group(1).lower(),
                                 enum.__name__)
        )

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
    """Declarative enumeration."""

    _reg = {}

    @classmethod
    def from_string(cls, string):
        """Get enum value from string"""
        try:
            return cls._reg[string]
        except KeyError:
            raise ValueError(
                "Invalid value for %r: %r" % (cls.__name__, string))

    @classmethod
    def values(cls):
        """Return enumeration values."""
        return cls._reg.keys()

    @classmethod
    def db_type(cls):
        """Provide database column type for use in table column definitions."""
        return DeclarativeEnumType(cls)
