"""Declarative base class/factory and query property support.
"""

from sqlalchemy import inspect, orm
from sqlalchemy.ext.declarative import declarative_base, DeclarativeMeta

from . import query, events
from .utils import (
    classproperty, is_sequence, has_primary_key, camelcase_to_underscore)
from ._compat import iteritems


class ModelMeta(DeclarativeMeta):
    """ModelBase's metaclass which provides:

        - Tablename autogeneration
        - Multiple database binding
        - Declarative ORM events
    """
    def __new__(mcs, name, bases, dct):
        # Determine if primary key is defined for dct or any of its bases.
        base_dcts = [dct] + [base.__dict__ for base in bases]

        if (not dct.get('__tablename__')
                and dct.get('__table__') is None
                and any([has_primary_key(base) for base in base_dcts])):
            # Set to underscore version of class name.
            dct['__tablename__'] = camelcase_to_underscore(name)

        # Set __events__ to expected default so that it's updatable when
        # initializing. E.g. if class definition sets __events__=None but
        # defines decorated events, then we want the final __events__ attribute
        # to reflect the registered events. If set to anything that's
        # non-empty/non-dict will lead to an error if decorated events defined.
        if not dct.get('__events__'):
            dct['__events__'] = {}

        return DeclarativeMeta.__new__(mcs, name, bases, dct)

    def __init__(cls, name, bases, dct):
        bind_key = dct.pop('__bind_key__', None)

        DeclarativeMeta.__init__(cls, name, bases, dct)

        if bind_key is not None:
            cls.__table__.info['bind_key'] = bind_key

        events.register(cls, dct)


class ModelBase(object):
    """Augmentable Base class for adding shared model properties/functions"""

    # default table args
    __table_args__ = {}

    # define a default order by when not specified by query operation
    # eg: { 'order_by': [column1, column2] }
    __mapper_args__ = {}

    # register orm event listeners
    __events__ = {}

    # query class to use for self.query
    query_class = query.QueryModel

    # An instance of `query_class`.
    # Can be used to query the database for instances of this model
    # Note: requires setting Class.query = QueryProperty(session) when session
    # available. See `make_declarative_base()` for automatic implementation.
    query = None

    def __init__(self, *args, **kargs):
        self.update(*args, **kargs)

    def __repr__(self):  # pragma: no cover
        values = ', '.join(['{0}={1}'.format(c, repr(getattr(self, c)))
                            for c in self.columns])
        return '<{0}({1})>'.format(self.__class__.__name__, values)

    def update(self, data_dict=None, strict=False, **kargs):
        """Update model with arbitrary set of data."""

        data = data_dict if isinstance(data_dict, dict) else kargs

        updatable_fields = self.strict_update_fields if strict else data.keys()
        relationships = self.relationships

        for field, value in iteritems(data):
            if hasattr(self, field) and field in updatable_fields:
                # consider v a dict if any of its elements are a dict
                if is_sequence(value):
                    is_dict = any([isinstance(val, dict) for val in value])
                else:
                    is_dict = isinstance(value, dict)

                attr = getattr(self, field)

                if (hasattr(attr, 'update')
                        and is_dict
                        and not isinstance(attr, dict)):
                    # nest calls to attr.update
                    attr.update(value)
                else:
                    if field in relationships and is_dict and not value:
                        # If v is {} and we're trying to update a relationship
                        # attribute, then we need to set to None to nullify
                        # relationship value.
                        value = None
                    setattr(self, field, value)

    @property
    def __to_dict__(self):
        """Configuration for `to_dict()`. Do any necessary preprocessing and
        return a set of string attributes which represent the fields which
        should be returned when calling `to_dict()`.

        By default this model is refreshed if it's __dict__ state is empty and
        only the ORM descriptor fields are returned.

        This is the property to override if you want to return more/less than
        the default ORM descriptor fields.

        Generally, we can usually rely on `self.__dict__` as a representation
        of model when it's just been loaded from the database. In this case,
        whatever values are present in `__dict__` are the loaded values from
        the database which include/exclude lazy attributes (columns and
        relationships).

        One issue to be aware of is that after a model has been committed (or
        expired), __dict__ will be empty. This can be worked around by calling
        `self.refresh()` which will reload the data from the database using the
        default loader strategies.

        These are the two main cases this default implementation will try to
        cover. For anything more complex it would be best to override this
        property or the `to_dict()` method itself.
        """
        if not self.descriptor_dict.keys() and orm.object_session(self):
            # if the descriptor dict keys are empty, assume we need to refresh
            self.refresh()

        return set(self.descriptor_dict.keys())

    @property
    def descriptor_dict(self):
        """Return `self.__dict__` key-filtered by `self.descriptors`"""
        return dict([(key, value)
                     for key, value in iteritems(self.__dict__)
                     if key in self.descriptors])

    def to_dict(self):
        """Return dict representation of model by filtering fields using
        `self.__to_dict__`.
        """
        data = {}
        data_fields = self.__to_dict__

        for field in data_fields:
            value = getattr(self, field)

            # Nest calls to `to_dict`. Try to find method on base value,
            # sequence values, or dict values.
            if hasattr(value, 'to_dict'):
                value = value.to_dict()
            elif is_sequence(value):
                value = [v.to_dict() if hasattr(v, 'to_dict') else v
                         for v in value]
            elif isinstance(value, dict):
                value = dict([(k, v.to_dict() if hasattr(v, 'to_dict') else v)
                              for k, v in iteritems(value)])

            data[field] = value

        return data

    def __iter__(self):
        """Implement __iter__ so model can be converted to dict via dict()."""
        return iteritems(self.to_dict())

    @property
    def strict_update_fields(self):
        """Model fields which are allowed to be updated during strict mode.
        Default is to limit to table columns. Override as needed in child
        class.
        """
        return self.columns

    ##
    # session based methods/properties
    ##

    @property
    def object_session(self):
        """Return session belonging to self"""
        return orm.object_session(self)

    @classproperty
    def session(cls):
        """Return session from query property"""
        return cls.query.session

    def flush(self, *args, **kargs):
        """Call `session.flush` on `self`"""
        self.session.flush([self], *args, **kargs)

    def save(self, *args, **kargs):
        """Call `session.add` on `self`"""
        self.session.add(self, *args, **kargs)

    def delete(self, *args, **kargs):
        """Call `session.delete` on `self`"""
        return self.session.delete(self, *args, **kargs)

    def expire(self, *args, **kargs):
        """Call `session.expire` on `self`"""
        self.session.expire(self, *args, **kargs)

    def refresh(self, *args, **kargs):
        """Call `session.refresh` on `self`"""
        self.session.refresh(self, *args, **kargs)

    def expunge(self, *args, **kargs):
        """Call `session.expunge` on `self`"""
        self.session.expunge(self, *args, **kargs)

    @classmethod
    def get(cls, *args, **kargs):
        """Proxy to query.get()"""
        return cls.query.get(*args, **kargs)

    @classmethod
    def get_by(cls, data_dict=None, **kargs):
        """Return first instance filtered by values using query.filter_by()"""
        data = data_dict if isinstance(data_dict, dict) else kargs
        return cls.query.filter_by(**data).first()

    ##
    # inspect based methods/properties
    ##

    @classproperty
    def primary_key(cls):
        """Return primary key as either single column (one primary key) or
        tuple otherwise.
        """
        primary = inspect(cls).primary_key

        if len(primary) == 1:
            primary = primary[0]

        return primary

    @classproperty
    def primary_keys(cls):
        """Return primary keys as tuple."""
        return inspect(cls).primary_key

    @classproperty
    def attrs(cls):
        """Return ORM attributes"""
        return inspect(cls).attrs.keys()

    @classproperty
    def descriptors(cls):
        """Return all ORM descriptors"""
        return [descr for descr in inspect(cls).all_orm_descriptors.keys()
                if not descr.startswith('__')]

    @classproperty
    def relationships(cls):
        """Return ORM relationships"""
        return inspect(cls).relationships.keys()

    @classproperty
    def column_attrs(cls):
        """Return table columns as list of class attributes at the class level.
        """
        return inspect(cls).column_attrs

    @classproperty
    def columns(cls):
        """Return table columns"""
        return inspect(cls).columns.keys()


def make_declarative_base(session=None, Model=None, Base=None):
    """Factory function for either creating a new declarative base class or
    extending a previously defined one.
    """
    if Model is None:
        Base = Base or ModelBase
        Model = declarative_base(
            cls=Base, constructor=Base.__init__, metaclass=ModelMeta)

    extend_declarative_base(Model, session)

    return Model


def extend_declarative_base(Model, session=None):
    """Extend a declarative base class with additional properties.

    - Extend `Model` with query property accessor
    """
    # Attach query attribute to Model if `session` object passed in.
    if session:
        Model.query = query.QueryProperty(session)
