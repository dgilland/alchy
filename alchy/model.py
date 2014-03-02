
import functools
from collections import namedtuple

import sqlalchemy
from sqlalchemy import inspect, orm, and_, or_
from sqlalchemy.ext.declarative import declarative_base, DeclarativeMeta
import six

from alchy import query, events
from alchy.utils import classproperty, is_sequence, has_primary_key, camelcase_to_underscore


class ModelMeta(DeclarativeMeta):
    def __new__(cls, name, bases, dct):
        # set __tablename__ (if not defined) to underscore version of class name
        if not dct.get('__tablename__') and not dct.get('__table__') is not None and has_primary_key(dct):
            dct['__tablename__'] = camelcase_to_underscore(name)

        # set __events__ to expected default so that it's updatable when initializing
        # e.g. if class definition sets __events__=None but defines decorated events,
        # then we want the final __events__ attribute to reflect the registered events.
        # if set to anything that's non-empty/non-dict will lead to an error if decorated events defined
        if not dct.get('__events__'):
            dct['__events__'] = {}

        return DeclarativeMeta.__new__(cls, name, bases, dct)

    def __init__(cls, name, bases, dct):
        super(ModelMeta, cls).__init__(name, bases, dct)
        events.register(cls, dct)


class ModelBase(object):
    '''Augmentable Base class for adding shared model properties/functions'''

    # default table args
    __table_args__ = {}

    # define a default order by when not specified by query operation
    # eg: { 'order_by': [column1, column2] }
    __mapper_args__ = {}

    # register orm event listeners
    __events__ = {}

    # query class to use for self.query
    query_class = query.Query

    # an instance of `query_class`
    # can be used to query the database for instances of this model
    # @note: requires setting Class.query = QueryProperty(session) when session available
    # see `make_declarative_base()` for automatic implementation
    query = None

    # specify sqla.session.query.filter() options for advanced and simple searches
    # eg: { key: lambda value: Model.column_name == val }
    __advanced_search__ = {}
    __simple_search__ = {}

    def __init__(self, *args, **kargs):
        self.update(*args, **kargs)

    def __repr__(self):  # pragma: no cover
        '''Default representation of model'''
        values = ', '.join(['{0}={1}'.format(c, repr(getattr(self, c))) for c in self.columns])
        return '<{0}({1})>'.format(self.__class__.__name__, values)

    def update(self, data_dict=None, strict=False, **kargs):
        '''
        Update model with arbitrary set of data
        '''

        data = data_dict if isinstance(data_dict, dict) else kargs

        updatable_fields = self.strict_update_fields if strict else data.keys()
        relationships = self.relationships

        for k, v in six.iteritems(data):
            if hasattr(self, k) and k in updatable_fields:
                # consider v a dict if any of its elements are a dict
                v_is_dict = any([isinstance(_v, dict) for _v in v]) if is_sequence(v) else isinstance(v, dict)

                attr = getattr(self, k)

                if hasattr(attr, 'update') and v_is_dict:
                    # nest calls to attr.update if available and input is a data dict
                    attr.update(v)
                else:
                    if k in relationships and v_is_dict and not v:
                        # typically, if v is {}, then we're usually updating a relationship attribute
                        # where the relationship has an empty/null value in the database
                        # (e.g. a frontend sends missing relationship attribute as {})
                        # but if we set a relationship attribute = {}, things blow up
                        # so instead, convert {} to None which is valid for standard relationship attribute
                        v = None
                    setattr(self, k, v)

    def to_dict(self, refresh_on_empty=True):
        '''
        Return dict representation of model.

        Drill down to any relationships and serialize those too.

        Assume that the current object has been loaded (lazy/joined/etc)
        and don't try to expand anything, i.e., just serialize the
        currently loaded data.

        However, with one exception: refresh if current __dict__ is empty.
        '''
        d = {}
        descriptors = self.descriptors

        for field, value in six.iteritems(self.__dict__):
            if field not in descriptors:
                # skip non-descriptors
                continue

            if hasattr(value, 'to_dict'):
                value = value.to_dict()
            elif is_sequence(value):
                value = [v.to_dict() if hasattr(v, 'to_dict') else v for v in value]

            d[field] = value

        if not d and refresh_on_empty and self.session:
            # Model's __dict__ is empty but has a session associated with it.
            # Most likely the model was previously committed which resets the __dict__ state.
            # Refreshing from database will repopulate the model's __dict__.
            self.refresh()
            d = self.to_dict(refresh_on_empty=False)

        return d

    def __iter__(self):
        '''Implement __iter__ so model can be converted to dict via dict(model)'''
        return six.iteritems(self.to_dict())

    @property
    def strict_update_fields(self):
        '''
        Model fields which are allowed to be updated during strict mode

        Default is to limit to table columns
        Override as needed in child classes
        '''
        return self.columns

    ##
    # search/filtering methods
    ##

    @classmethod
    def get_search(cls, search_dict, filter_fns):
        filters = []

        for key, filter_fn in [(k, v) for k, v in six.iteritems(filter_fns) if k in search_dict]:
            filters.append(filter_fn(search_dict[key]))

        return filters

    @classmethod
    def advanced_search(cls, search_dict):
        filters = None
        if cls.__advanced_search__:
            _filters = cls.get_search(search_dict, cls.__advanced_search__)

            if _filters:
                filters = and_(*_filters)

        return filters

    @classmethod
    def simple_search(cls, search_string):
        filters = None

        if cls.__simple_search__:
            terms = [s for s in search_string.split()]
            fields = cls.__simple_search__.keys()
            field_count = len(fields)

            search_filters = []

            for term in terms:
                # create a dict with each `config_search` key and `term` so filters can be applied to each combination
                # i.e. { config_search_key1: term, config_search_key2: term, ..., config_search_keyN, term }
                search_dict = dict(zip(fields, [term] * field_count))
                term_filters = cls.get_search(search_dict, cls.__simple_search__)

                if term_filters:
                    # `or` filters together since only 1 filter needs to match for `term`
                    search_filters.append(or_(*term_filters))

            if search_filters:
                # `and` all search conditions together
                # each `term` should have an OR'd set of filters that evaluates to True
                filters = and_(*search_filters)

        return filters

    ##
    # session based methods/properties
    ##

    @property
    def session(self):
        '''Return session belonging to self'''
        return orm.object_session(self)

    def flush(self, *args, **kargs):
        self.session.flush([self], *args, **kargs)

    def save(self, *args, **kargs):
        self.session.add(self, *args, **kargs)

    def delete(self, *args, **kargs):
        return self.session.delete(self, *args, **kargs)

    def expire(self, *args, **kargs):
        self.session.expire(self, *args, **kargs)

    def refresh(self, *args, **kargs):
        self.session.refresh(self, *args, **kargs)

    def expunge(self, *args, **kargs):
        self.session.expunge(self, *args, **kargs)

    @classmethod
    def get(cls, *args, **kargs):
        '''Proxy to query.get()'''
        return cls.query.get(*args, **kargs)

    @classmethod
    def get_by(cls, data_dict=None, **kargs):
        '''Return first instance filtered by values using query.filter_by()'''
        data = data_dict if isinstance(data_dict, dict) else kargs
        return cls.query.filter_by(**data).first()

    ##
    # inspect based methods/properties
    ##

    @classproperty
    def primary_key(cls):
        '''Return primary key as either single column (one primary key) or tuple otherwise.'''
        primary = inspect(cls).primary_key

        if len(primary) == 1:
            primary = primary[0]

        return primary

    @classproperty
    def attrs(cls):
        '''Return ORM attributes'''
        return inspect(cls).attrs.keys()

    @classproperty
    def descriptors(cls):
        '''Return all ORM descriptors'''
        return [d for d in inspect(cls).all_orm_descriptors.keys() if not d.startswith('__')]

    @classproperty
    def relationships(cls):
        '''Return ORM relationships'''
        return inspect(cls).relationships.keys()

    @classproperty
    def column_attrs(cls):
        '''Return table columns as list of class attributes at the class level'''
        return inspect(cls).column_attrs

    @classproperty
    def columns(cls):
        '''Return table columns'''
        return inspect(cls).columns.keys()


class QueryProperty(object):
    def __init__(self, session):
        self.session = session

    def __get__(self, model, Model):
        mapper = orm.class_mapper(Model)
        if mapper:
            if not getattr(Model, 'query_class', None):
                Model.query_class = query.Query

            q = Model.query_class(mapper, session=self.session())
            q.__model__ = Model

            return q


def make_declarative_base(session=None, query_property=None, Model=None, Base=None):
    if Model is None:
        Base = Base or ModelBase
        Model = declarative_base(cls=Base, constructor=Base.__init__, metaclass=ModelMeta)

    extend_declarative_base(Model, session, query_property)
    return Model


def extend_declarative_base(Model, session=None, query_property=None):
    # attach query attribute to Model if `session` object passed in
    if session:
        Model.query = query_property(session) if query_property else QueryProperty(session)
