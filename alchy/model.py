"""Declarative base for ORM models.
"""

from sqlalchemy import inspect, orm
from sqlalchemy.ext.declarative import (
    declarative_base,
    DeclarativeMeta,
    declared_attr,
)

from . import query, events
from .utils import (
    is_sequence,
    camelcase_to_underscore,
    get_mapper_class,
    merge_declarative_args,
    should_set_tablename,
)
from ._compat import iteritems


__all__ = [
    'ModelMeta',
    'ModelBase',
    'make_declarative_base',
    'extend_declarative_base',
]


class ModelMeta(DeclarativeMeta):
    """ModelBase's metaclass which provides:

    - Tablename autogeneration when ``__tablename__`` not defined.
    - Support for multiple database bindings via \
    :attr:`ModelBase.__bind_key__`.
    - Support for declarative ORM events via :mod:`alchy.events` decorators \
    or :attr:`ModelBase.__events__`.
    """
    def __new__(mcs, name, bases, dct):
        # Set __events__ to expected default so that it's updatable when
        # initializing. E.g. if class definition sets __events__=None but
        # defines decorated events, then we want the final __events__ attribute
        # to reflect the registered events. If set to anything that's
        # non-empty/non-dict will lead to an error if decorated events defined.
        if not dct.get('__events__'):
            dct['__events__'] = {}

        if '__bind_key__' not in dct:
            base_dcts = [dct] + [base.__dict__ for base in bases]
            for base in base_dcts:
                if '__bind_key__' in base:
                    dct['__bind_key__'] = base['__bind_key__']
                    break

        cls = DeclarativeMeta.__new__(mcs, name, bases, dct)

        # Determine if should set __tablename__.
        # This is being done after DeclarativeMeta.__new__()
        # as the class is needed to accommodate @declared_attr columns.
        if should_set_tablename(cls):
            # Set to underscore version of class name.
            cls.__tablename__ = camelcase_to_underscore(name)

        return cls

    def __init__(cls, name, bases, dct):
        DeclarativeMeta.__init__(cls, name, bases, dct)

        if hasattr(cls, '__table__'):
            if '__bind_key__' in dct:
                cls.__table__.info['bind_key'] = dct['__bind_key__']

            events.register(cls, dct)


class ModelBase(object):
    """Base class for creating a declarative base for models.

    To create a declarative base::

        # in project/core.py
        from alchy import ModelBase, make_declarative_base

        class Base(ModelBase):
            # augument the ModelBase with super powers
            pass

        Model = make_declarative_base(Base=Base)


        # in project/models/user.py
        from project.core import Model

        class User(Model):
            # define declarative User model
            pass


    Attributes:

        __table_args__: Default table args.

        __mapper_args__: Define a default order by when not specified by query
            operation, e.g.: ``{ 'order_by': [column1, column2] }``

        __bind_key__: Bind a model to a particular database URI using keys from
            ``Manager.config['SQLALCHEMY_BINDS']``. By default a model will be
            bound to ``Manager.config['SQLALCHEMY_DATABASE_URI']``.

        __events__: Register orm event listeners. See :mod:`alchy.events` for
            more details.

        query_class: Query class to use for ``self.query``.

        query: An instance of :attr:`query_class`. Can be used to query the
            database for instances of this model. NOTE: Requires setting
            ``MyClass.query = QueryProperty(session)`` when session available.
            See :func:`make_declarative_base` for automatic implementation.
    """

    __bind_key__ = None
    __events__ = {}
    query_class = query.QueryModel
    query = None

    @declared_attr
    def __mapper_args__(cls):  # pylint: disable=no-self-argument
        _, kargs = merge_declarative_args(cls,
                                          '__global_mapper_args__',
                                          '__local_mapper_args__')
        return kargs

    @declared_attr
    def __table_args__(cls):  # pylint: disable=no-self-argument
        args, kargs = merge_declarative_args(cls,
                                             '__global_table_args__',
                                             '__local_table_args__')
        # Append kargs onto end of args to adhere to SQLAlchemy requirements.
        args.append(kargs)
        return tuple(args)

    def __init__(self, *args, **kargs):
        """Initialize model instance by calling :meth:`update`."""
        self.update(*args, **kargs)

    def __repr__(self):  # pragma: no cover
        values = ', '.join(['{0}={1}'.format(c, repr(getattr(self, c)))
                            for c in self.columns()])
        return '<{0}({1})>'.format(self.__class__.__name__, values)

    def __getitem__(self, item):
        """Proxy getitem to getattr."""
        return getattr(self, item)

    def __setitem__(self, item, value):
        """Proxy setitem to setattr."""
        setattr(self, item, value)

    def update(self, data_dict=None, **kargs):
        """Update model with arbitrary set of data."""

        data = data_dict if isinstance(data_dict, dict) else kargs

        for field, value in iteritems(data):
            if hasattr(self, field):
                self._set_field(field, value)

    def _set_field(self, field, value):
        """Set model field with value."""
        # Consider value a dict if any of its elements are a dict.
        if is_sequence(value):
            is_dict = any([isinstance(val, dict) for val in value])
        else:
            is_dict = isinstance(value, dict)

        attr = getattr(self, field)

        if (hasattr(attr, 'update') and
                value and
                is_dict and
                not isinstance(attr, dict)):
            # Nest calls to attr.update.
            attr.update(value)
        else:
            if field in self.relationships():
                self._set_relationship_field(field, value)
            else:
                setattr(self, field, value)

    def _set_relationship_field(self, field, value):
        """Set model relationships field with value."""
        relationship_class = get_mapper_class(self.__class__, field)
        is_sequence_relationship = is_sequence(getattr(self, field))

        if is_sequence_relationship and is_sequence(value):
            # Convert each value instance to relationship class.
            value = [relationship_class(val) if isinstance(val, dict)
                     else val
                     for val in value]
        elif not value and isinstance(value, dict):
            # If value is {} and we're trying to update a relationship
            # attribute, then we need to set to None to nullify relationship
            # value.
            value = None
        elif not is_sequence_relationship and isinstance(value, dict):
            # Convert single value to relationship class.
            value = relationship_class(value)

        setattr(self, field, value)

    @property
    def __to_dict__(self):
        """Configuration for :meth:`to_dict`. Do any necessary preprocessing
        and return a set of string attributes which represent the fields which
        should be returned when calling :meth:`to_dict`.

        By default this model is refreshed if it's ``__dict__`` state is empty
        and only the ORM descriptor fields are returned.

        This is the property to override if you want to return more/less than
        the default ORM descriptor fields.

        Generally, we can usually rely on ``__dict__`` as a representation of
        model when it's just been loaded from the database. In this case,
        whatever values are present in ``__dict__`` are the loaded values
        from the database which include/exclude lazy attributes (columns and
        relationships).

        One issue to be aware of is that after a model has been committed (or
        expired), ``__dict__`` will be empty. This can be worked around by
        calling :meth:`refresh` which will reload the data from the database
        using the default loader strategies.

        These are the two main cases this default implementation will try to
        cover. For anything more complex it would be best to override this
        property or the :meth:`to_dict` method itself.
        """
        if not self.descriptor_dict.keys() and orm.object_session(self):
            # If the descriptor dict keys are empty, assume we need to refresh.
            self.refresh()

        return set(self.descriptor_dict.keys())

    @property
    def descriptor_dict(self):
        """Return :attr:`__dict__` key-filtered by :attr:`descriptors`."""
        return dict([(key, value)
                     for key, value in iteritems(self.__dict__)
                     if key in self.descriptors()])

    def to_dict(self):
        """Return dict representation of model by filtering fields using
        :attr:`__to_dict__`.
        """
        data = {}
        relationships = self.relationships()

        for field in self.__to_dict__:
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
            elif field in relationships and value is None:
                value = {}

            data[field] = value

        return data

    def __iter__(self):
        """Implement ``__iter__`` so model can be converted to dict via
        ``dict()``.
        """
        return iteritems(self.to_dict())

    ##
    # session based methods/properties
    ##

    @property
    def object_session(self):
        """Return session belonging to ``self``"""
        return orm.object_session(self)

    @classmethod
    def session(cls):
        """Return session from query property"""
        return cls.query.session

    def flush(self, *args, **kargs):
        """Call ``session.flush()`` on ``self``"""
        self.session().flush([self], *args, **kargs)

    def save(self, *args, **kargs):
        """Call ``session.add()`` on ``self``"""
        self.session().add(self, *args, **kargs)

    def delete(self, *args, **kargs):
        """Call ``session.delete()`` on ``self``"""
        return self.session().delete(self, *args, **kargs)

    def expire(self, *args, **kargs):
        """Call ``session.expire()`` on ``self``"""
        self.session().expire(self, *args, **kargs)

    def refresh(self, *args, **kargs):
        """Call ``session.refresh()`` on ``self``"""
        self.session().refresh(self, *args, **kargs)

    def expunge(self, *args, **kargs):
        """Call ``session.expunge()`` on ``self``"""
        self.session().expunge(self, *args, **kargs)

    def is_modified(self, *args, **kargs):
        """Call ``session.is_modified()`` on ``self``"""
        return self.session().is_modified(self, *args, **kargs)

    @classmethod
    def get(cls, *args, **kargs):
        """Proxy to ``cls.query.get()``"""
        return cls.query.get(*args, **kargs)

    @classmethod
    def get_by(cls, data_dict=None, **kargs):
        """Return first instance filtered by values using
        ``cls.query.filter_by()``.
        """
        data = data_dict if isinstance(data_dict, dict) else kargs
        return cls.query.filter_by(**data).first()

    @classmethod
    def filter(cls, *args, **kargs):
        """Proxy to ``cls.query.filter()``"""
        return cls.query.filter(*args, **kargs)

    @classmethod
    def filter_by(cls, *args, **kargs):
        """Proxy to ``cls.query.filter_by()``"""
        return cls.query.filter_by(*args, **kargs)

    ##
    # SQLAlchemy.inspect() based methods/properties
    ##

    @classmethod
    def primary_key(cls):
        """Return primary key as either single column (one primary key) or
        tuple otherwise.
        """
        primary = inspect(cls).primary_key

        if len(primary) == 1:
            primary = primary[0]

        return primary

    @classmethod
    def primary_keys(cls):
        """Return primary keys as tuple."""
        return inspect(cls).primary_key

    @classmethod
    def primary_attrs(cls):
        """Return class attributes from primary keys."""
        primary_keys = cls.primary_keys()
        return [getattr(cls, attr)
                for attr in cls.columns()
                if getattr(cls, attr).property.columns[0] in primary_keys]

    @classmethod
    def attrs(cls):
        """Return ORM attributes"""
        # pylint: disable=no-member
        return inspect(cls).attrs.keys()

    @classmethod
    def descriptors(cls):
        """Return all ORM descriptors"""
        # pylint: disable=maybe-no-member
        return [descr for descr in inspect(cls).all_orm_descriptors.keys()
                if not descr.startswith('__')]

    @classmethod
    def relationships(cls):
        """Return ORM relationships"""
        # pylint: disable=no-member
        return inspect(cls).relationships.keys()

    @classmethod
    def column_attrs(cls):
        """Return table columns as list of class attributes at the class level.
        """
        return inspect(cls).column_attrs

    @classmethod
    def columns(cls):
        """Return table columns."""
        # pylint: disable=no-member
        return inspect(cls).columns.keys()


def make_declarative_base(session=None,
                          Model=None,
                          Base=None,
                          Meta=None,
                          metadata=None):
    """Factory function for either creating a new declarative base class or
    extending a previously defined one.
    """
    if Model is None:
        Base = Base or ModelBase
        Meta = Meta or ModelMeta
        Model = declarative_base(cls=Base,
                                 constructor=Base.__init__,
                                 metaclass=Meta,
                                 metadata=metadata)

    extend_declarative_base(Model, session)

    return Model


def extend_declarative_base(Model, session=None):
    """Extend a declarative base class with additional properties.

    - Extend `Model` with query property accessor
    """
    # Attach query attribute to Model if `session` object passed in.
    if session:
        Model.query = query.QueryProperty(session)
