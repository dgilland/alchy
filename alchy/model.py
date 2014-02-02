
from sqlalchemy import inspect, orm, and_, or_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.exc import UnmappedClassError

import query
from utils import classproperty, is_sequence

class ModelBase(object):
    '''Augmentable Base class for adding shared model properties/functions'''

    # default table args
    __table_args__ = {}

    # define a default order by when not specified by query operation
    # eg: { 'order_by': [column1, column2] }
    __mapper_args__ = {}

    # query class to use for self.query
    query_class = query.Query

    # an instance of `query_class`
    # can be used to query the database for instances of this model
    # @note: requires setting Class.query = QueryProperty(session) when session available
    # see `make_declarative_base()` for automatic implementation
    query = None

    # specify sqla.session.query.filter() options for advanced and simple searches
    # eg: { key: lambda value: Model.column_name == val }
    advanced_search_config = {}
    simple_search_config = {}

    def __init__(self, *args, **kargs):
        self.update(*args, **kargs)

    def __repr__(self):
        '''
        Default representation of model
        '''
        values = ', '.join(['{0}={1}'.format(c, repr(getattr(self, c))) for c in self.columns])
        return '<{0}({1})>'.format(self.__class__.__name__, values)

    def update(self, data_dict=None, strict=False, **kargs):
        '''
        Update model with arbitrary set of data
        '''

        data = data_dict if isinstance(data_dict, dict) else kargs

        updatable_fields = self.strict_update_fields if strict else data.keys()
        relationships = self.relationships

        for k,v in data.iteritems():
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

    def to_dict(self):
        '''
        Return dict representation of model.

        Drill down to any relationships and serialize those too.

        Assume that the current object has been loaded (lazy/joined/etc)
        and don't try to expand anything, i.e., just serialize the currently loaded data
        '''
        d = {}

        for field, value in self.__dict__.iteritems():
            if field.startswith('_sa'):
                # skip sqlalchemy properties
                continue

            d[field] = [v.to_dict() for v in value] if is_sequence(value) else value

        return d

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

        for key, filter_fn in [(k,v) for k,v in filter_fns.iteritems() if k in search_dict]:
            filters.append(filter_fn(search_dict[key]))

        return filters

    @classmethod
    def advanced_search(cls, search_dict):
        filters = None
        if cls.advanced_search_config:
            _filters = cls.get_search(search_dict, cls.advanced_search_config)

            if _filters:
                filters = and_(*_filters)

        return filters

    @classmethod
    def simple_search(cls, search_string):
        filters = None

        if cls.simple_search_config:
            terms = [s for s in search_string.split()]
            fields = cls.simple_search_config.keys()
            field_count = len(fields)

            search_filters = []

            for term in terms:
                # create a dict with each `config_search` key and `term` so filters can be applied to each combination
                # i.e. { config_search_key1: term, config_search_key2: term, ..., config_search_keyN, term }
                search_dict = dict(zip(fields, [term]*field_count))
                term_filters = cls.get_search(search_dict, cls.simple_search_config)

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
        return self.session.flush([self], *args, **kargs)

    def delete(self, *args, **kargs):
        return self.session.delete(self, *args, **kargs)

    def expire(self, *args, **kargs):
        return self.session.expire(self, *args, **kargs)

    def refresh(self, *args, **kargs):
        return self.session.refresh(self, *args, **kargs)

    def expunge(self, *args, **kargs):
        return self.session.expunge(self, *args, **kargs)

    @classmethod
    def get(cls, *args, **kargs):
        return cls.query.get(*args, **kargs)

    ##
    # inspect based methods/properties
    ##

    @classproperty
    def attrs(cls):
        '''Return ORM attributes'''
        return inspect(cls).attrs.keys()

    @classproperty
    def descriptors(cls):
        '''Return all ORM descriptors'''
        return [d for d in inspect(cls).mapper.all_orm_descriptors.keys() if not d.startswith('__')]

    @classproperty
    def relationships(cls):
        '''Return ORM relationships'''
        return inspect(cls).mapper.relationships.keys()

    @classproperty
    def column_attrs(cls):
        '''Return table columns as list of class attributes at the class level'''
        return inspect(cls).mapper.column_attrs

    @classproperty
    def columns(cls):
        '''Return table columns'''
        return inspect(cls).mapper.columns.keys()

class QueryProperty(object):
    def __init__(self, session):
        self.session = session

    def __get__(self, model, Model):
        try:
            mapper = orm.class_mapper(Model)
            if mapper:
                if not getattr(Model, 'query_class', None):
                    Model.query_class = query.Query

                q = Model.query_class(mapper, session=self.session())
                q.__model__ = Model

                return q
        except UnmappedClassError:
            return None

def make_declarative_base(session=None, query_property=None):
    Base = declarative_base(cls=ModelBase, constructor=ModelBase.__init__)
    extend_declarative_base(Base, session, query_property)
    return Base

def extend_declarative_base(Base, session=None, query_property=None):
    # attach query attribute to Base if `session` object passed in
    if session:
        Base.query = query_property(session) if query_property else QueryProperty(session)

    return Base

