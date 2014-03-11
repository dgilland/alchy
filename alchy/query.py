'''Query subclass used by Manager as default session query class.
'''

from math import ceil

from sqlalchemy import orm, and_, or_, inspect
from sqlalchemy.orm.strategy_options import Load


class Query(orm.Query):
    '''Extension of default Query class used in SQLAlchemy session queries.
    '''

    # when used as a query property (e.g. MyModel.query), then this is populated with the originating model
    __model__ = None

    DEFAULT_PER_PAGE = 50

    @property
    def Model(self):
        '''Return originating model class when Query used a query property'''
        return self.__model__

    @property
    def entities(self):
        '''Return list of entity classes present in query'''
        return [e.mapper.class_ for e in self._entities]

    @property
    def join_entities(self):
        '''Return list of the joined entity classes present in query'''
        return [e.mapper.class_ for e in self._join_entities]

    @property
    def all_entities(self):
        '''Return list of entities + join_entities present in query'''
        return self.entities + self.join_entities

    def _join_eager(self, keys, outerjoin, **kargs):
        '''Helper method for applying join()/outerjoin() with contains_eager()'''
        alias = kargs.pop('alias', None)

        key = keys[0]
        path_keys = keys[1:]

        join_args = ([alias, key] if alias else [key]) + list(path_keys)

        opt = orm.contains_eager(key, alias=alias)

        for k in path_keys:
            opt = opt.contains_eager(k)

        join = self.outerjoin if outerjoin else self.join

        return join(*join_args).options(opt)

    def join_eager(self, *keys, **kargs):
        '''Apply `self.join()` + `self.options(contains_eager())`.'''
        return self._join_eager(keys, False, **kargs)

    def outerjoin_eager(self, *keys, **kargs):
        '''Apply `self.outerjoin()` + `self.options(contains_eager())`.'''
        return self._join_eager(keys, True, **kargs)

    def _join_load(self, keys, load_type, **kargs):
        '''Helper method for returning load strategies.'''
        opt = getattr(orm, load_type)(keys[0], **kargs)

        for k in keys[1:]:
            opt = getattr(opt, load_type)(k)

        return self.options(opt)

    def joinedload(self, *keys, **kargs):
        '''Apply joinedload() to `keys`'''
        return self._join_load(keys, 'joinedload', **kargs)

    def immediateload(self, *keys, **kargs):
        '''Apply immediateload() to `keys`'''
        return self._join_load(keys, 'immediateload', **kargs)

    def lazyload(self, *keys, **kargs):
        '''Apply lazyload() to `keys`'''
        return self._join_load(keys, 'lazyload', **kargs)

    def noload(self, *keys, **kargs):
        '''Apply noload() to `keys`'''
        return self._join_load(keys, 'noload', **kargs)

    def subqueryload(self, *keys, **kargs):
        '''Apply subqueryload() to `keys`'''
        return self._join_load(keys, 'subqueryload', **kargs)

    def load_only(self, *columns):
        '''Apply `load_only()` to query'''
        obj, columns = get_load_options(*columns)
        return self.options(obj.load_only(*columns))

    def defer(self, *columns):
        '''Apply `defer()` to query'''
        obj, columns = get_load_options(*columns)
        opts = obj
        for column in columns:
            opts = opts.defer(column)
        return self.options(opts)

    def undefer(self, *columns):
        '''Apply `undefer()` to query'''
        obj, columns = get_load_options(*columns)
        opts = obj
        for column in columns:
            opts = opts.undefer(column)
        return self.options(opts)

    def undefer_group(self, *names):
        '''Apply `undefer_group()` to query'''
        obj, names = get_load_options(*names)
        return self.options(obj.undefer_group(names[0]))

    def map(self, func):
        '''Call native `map` on `self.all()`'''
        return [func(item) for item in self.all()]

    def reduce(self, func, initial=None, reverse=False):
        '''Reduce `self.all()` using `func`'''
        items = self.all()

        if reverse:
            items = reversed(items)

        result = initial
        for item in items:
            result = func(result, item)
        return result

    def reduce_right(self, func, initial=None):
        '''Reduce reversed `self.all()` using `func`'''
        return self.reduce(func, initial=initial, reverse=True)

    def pluck(self, column):
        '''Pluck `column` attribute values from `self.all()` results and return as list'''
        return [getattr(r, column, None) for r in self.all()]

    def page(self, page=1, per_page=None):
        '''Return query with limit and offset applied for page'''
        if per_page is None:
            per_page = self.DEFAULT_PER_PAGE

        return self.limit(per_page).offset((page - 1) * per_page)

    def paginate(self, page=1, per_page=None, error_out=True):
        '''Return Pagination instance using already defined query parameters.'''
        if error_out and page < 1:
            raise IndexError

        if per_page is None:
            per_page = self.DEFAULT_PER_PAGE

        items = self.page(page, per_page).all()

        if not items and page != 1 and error_out:
            raise IndexError

        # No need to count if we're on the first page and there are fewer items than we expected.
        if page == 1 and len(items) < per_page:
            total = len(items)
        else:
            total = self.order_by(None).count()

        return Pagination(self, page, per_page, total, items)

    def advanced_search(self, search_dict):
        '''Apply advanced search filters given `search_dict`.'''
        filters = [m for m in [model.advanced_search(search_dict) for model in self.all_entities] if m is not None]
        return self.filter(and_(*filters)) if filters else self

    def simple_search(self, search_string):
        '''Apply simple search filters given `search_string`.'''
        filters = [m for m in [model.simple_search(search_string) for model in self.all_entities] if m is not None]
        return self.filter(or_(*filters)) if filters else self

    def search(self, search_string=None, search_dict=None, limit=None, offset=None):
        '''Perform combination of simple/advanced searching with optional limit/offset support.'''
        query = self

        if search_string is not None:
            query = query.simple_search(search_string)

        if search_dict is not None:
            query = query.advanced_search(search_dict)

        if limit is not None:
            query = query.limit(limit)

        if offset is not None:
            query = query.offset(offset)

        return query


##
# Pagination class and usage adapated from Flask-SQLAlchemy: https://github.com/mitsuhiko/flask-sqlalchemy
##


class Pagination(object):
    '''
    Internal helper class returned by `BaseQuery.paginate`.  You
    can also construct it from any other SQLAlchemy query object if you are
    working with other libraries.  Additionally it is possible to pass `None`
    as query object in which case the `prev` and `next` will
    no longer work.
    '''

    def __init__(self, query, page, per_page, total, items):
        # the unlimited query object that was used to create this pagination object
        self.query = query
        # the current page number (1 indexed)
        self.page = page
        # the number of items to be displayed on a page.
        self.per_page = per_page
        # the total number of items matching the query
        self.total = total
        # the items for the current page
        self.items = items

        # the total number of pages
        self.pages = 0 if self.per_page == 0 else int(ceil(self.total / float(self.per_page)))
        # number of the previous page
        self.prev_num = self.page - 1
        # True if a previous page exists
        self.has_prev = self.page > 1
        # number of the next page
        self.next_num = self.page + 1
        # True if a next page exists
        self.has_next = self.page < self.pages

    def prev(self, error_out=False):
        '''Returns a `Pagination` object for the previous page.'''
        assert self.query is not None, 'a query object is required for this method to work'
        return self.query.paginate(self.page - 1, self.per_page, error_out)

    def next(self, error_out=False):
        '''Returns a `Pagination` object for the next page.'''
        assert self.query is not None, 'a query object is required for this method to work'
        return self.query.paginate(self.page + 1, self.per_page, error_out)


def get_load_options(*columns):
    '''Helper method that attempts to extract a sqlalchemy object from `columns[0]`
    and return remaining columns to apply to a query load method.
    '''
    model_inspect = inspect(columns[0], raiseerr=False)

    # return an obj which has loading API
    if model_inspect and model_inspect.is_mapper:
        obj = Load(columns[0])
        columns = columns[1:]
    elif isinstance(columns[0], Load):
        obj = columns[0]
        columns = columns[1:]
    else:
        obj = orm

    return (obj, columns)
