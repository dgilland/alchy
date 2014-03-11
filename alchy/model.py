'''Declarative base class/factory and query property support.
'''

from sqlalchemy import inspect, orm, and_, or_
from sqlalchemy.ext.declarative import declarative_base, DeclarativeMeta

from alchy import query, events
from alchy.utils import classproperty, is_sequence, has_primary_key, camelcase_to_underscore
from alchy._compat import iteritems


class ModelMeta(DeclarativeMeta):
    '''ModelBase's metaclass which provides:

        - Tablename autogeneration
        - Declarative ORM events
    '''
    def __new__(mcs, name, bases, dct):
        # set __tablename__ (if not defined) to underscore version of class name
        if not dct.get('__tablename__') and not dct.get('__table__') is not None and has_primary_key(dct):
            dct['__tablename__'] = camelcase_to_underscore(name)

        # set __events__ to expected default so that it's updatable when initializing
        # e.g. if class definition sets __events__=None but defines decorated events,
        # then we want the final __events__ attribute to reflect the registered events.
        # if set to anything that's non-empty/non-dict will lead to an error if decorated events defined
        if not dct.get('__events__'):
            dct['__events__'] = {}

        return DeclarativeMeta.__new__(mcs, name, bases, dct)

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
        values = ', '.join(['{0}={1}'.format(c, repr(getattr(self, c))) for c in self.columns])
        return '<{0}({1})>'.format(self.__class__.__name__, values)

    def update(self, data_dict=None, strict=False, **kargs):
        '''Update model with arbitrary set of data.'''

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

                if hasattr(attr, 'update') and is_dict:
                    # nest calls to attr.update if available and input is a data dict
                    attr.update(value)
                else:
                    if field in relationships and is_dict and not value:
                        # typically, if v is {}, then we're usually updating a relationship attribute
                        # where the relationship has an empty/null value in the database
                        # (e.g. a frontend sends missing relationship attribute as {})
                        # but if we set a relationship attribute = {}, things blow up
                        # so instead, convert {} to None which is valid for standard relationship attribute
                        value = None
                    setattr(self, field, value)

    def to_dict(self, refresh_on_empty=True):
        '''Return dict representation of model.

        Drill down to any relationships and serialize those too.

        Assume that the current object has been loaded (lazy/joined/etc)
        and don't try to expand anything, i.e., just serialize the
        currently loaded data.

        However, with one exception: refresh if current __dict__ is empty.
        '''
        data = {}
        descriptors = self.descriptors

        for field, value in iteritems(self.__dict__):
            if field not in descriptors:
                # skip non-descriptors
                continue

            if hasattr(value, 'to_dict'):
                value = value.to_dict()
            elif is_sequence(value):
                value = [v.to_dict() if hasattr(v, 'to_dict') else v for v in value]

            data[field] = value

        if not data and refresh_on_empty and self.session:
            # Model's __dict__ is empty but has a session associated with it.
            # Most likely the model was previously committed which resets the __dict__ state.
            # Refreshing from database will repopulate the model's __dict__.
            self.refresh()
            data = self.to_dict(refresh_on_empty=False)

        return data

    def __iter__(self):
        '''Implement __iter__ so model can be converted to dict via dict(model)'''
        return iteritems(self.to_dict())

    @property
    def strict_update_fields(self):
        '''Model fields which are allowed to be updated during strict mode.

        Default is to limit to table columns. Override as needed in child class.
        '''
        return self.columns

    ##
    # search/filtering methods
    ##

    @classmethod
    def get_search(cls, search_dict, filter_fns):
        '''Generic helper for applying a key-pairs from `search_dict` to key-pairs from `filter_fns`
        where keys are equal.
        '''
        filters = []

        for key, filter_fn in [(k, v) for k, v in iteritems(filter_fns) if k in search_dict]:
            filters.append(filter_fn(search_dict[key]))

        return filters

    @classmethod
    def advanced_search(cls, search_dict):
        '''Return set of filters generated from passing each key-pair from `search_dict` to
        the filter functions defined in `cls.__advanced_search__`.
        '''
        filters = None
        if cls.__advanced_search__:
            _filters = cls.get_search(search_dict, cls.__advanced_search__)

            if _filters:
                filters = and_(*_filters)

        return filters

    @classmethod
    def simple_search(cls, search_string):
        '''Return set of filters generated from passing each space-delimited search term
        from `search_string` to the filter functions defined in `cls.__simple_search__`.
        '''
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
        '''Call `session.flush` on `self`'''
        self.session.flush([self], *args, **kargs)

    def save(self, *args, **kargs):
        '''Call `session.add` on `self`'''
        self.session.add(self, *args, **kargs)

    def delete(self, *args, **kargs):
        '''Call `session.delete` on `self`'''
        return self.session.delete(self, *args, **kargs)

    def expire(self, *args, **kargs):
        '''Call `session.expire` on `self`'''
        self.session.expire(self, *args, **kargs)

    def refresh(self, *args, **kargs):
        '''Call `session.refresh` on `self`'''
        self.session.refresh(self, *args, **kargs)

    def expunge(self, *args, **kargs):
        '''Call `session.expunge` on `self`'''
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
        return [descr for descr in inspect(cls).all_orm_descriptors.keys() if not descr.startswith('__')]

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
    '''Query property accessor which gives a model access to query capabilities
    via Model.query which is equivalent to session.query(Model)
    '''
    def __init__(self, session):
        self.session = session

    def __get__(self, model, Model):
        mapper = orm.class_mapper(Model)
        if mapper:
            if not getattr(Model, 'query_class', None):
                Model.query_class = query.Query

            query_property = Model.query_class(mapper, session=self.session())
            query_property.__model__ = Model

            return query_property


def make_declarative_base(session=None, query_property=None, Model=None, Base=None):
    '''Factory function for either creating a new declarative base class or extending
    a previously defined one.
    '''
    if Model is None:
        Base = Base or ModelBase
        Model = declarative_base(cls=Base, constructor=Base.__init__, metaclass=ModelMeta)

    extend_declarative_base(Model, session, query_property)
    return Model


def extend_declarative_base(Model, session=None, query_property=None):
    '''Extend a declarative base class with additional properties.

    - Extend `Model` with query property accessor
    '''
    # attach query attribute to Model if `session` object passed in
    if session:
        Model.query = query_property(session) if query_property else QueryProperty(session)
