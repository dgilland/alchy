"""Query subclass used by Manager as default session query class.
"""

from math import ceil

from sqlalchemy import orm, and_, or_, inspect

try:
    from sqlalchemy.orm.strategy_options import Load
except ImportError:  # pragma: no cover
    import warnings
    from sqlalchemy import __version__ as sqla_version

    warn_msg = ('The installed version of SQLAlchemy=={0} is not compatible '
                'with the alchy.Query loading API. '
                'Use with caution!').format(sqla_version)

    warnings.warn(warn_msg, RuntimeWarning)

    class Load(object):
        """Dummy Load class which just fails when used."""
        def __call__(self, *args, **kargs):
            raise NotImplementedError(warn_msg)

        def __getattr__(self, attr):
            self()

from ._compat import iteritems
from .utils import join_subquery_on_columns


class Query(orm.Query):
    """Extension of default Query class used in SQLAlchemy session queries.
    """

    # Default per_page argument for pagination when per_page not specified.
    DEFAULT_PER_PAGE = 50

    @property
    def entities(self):
        """Return list of entity classes present in query"""
        return [e.mapper.class_ for e in self._entities]

    @property
    def join_entities(self):
        """Return list of the joined entity classes present in query"""
        return [e.mapper.class_ for e in self._join_entities]

    @property
    def all_entities(self):
        """Return list of entities + join_entities present in query"""
        return self.entities + self.join_entities

    def _join_eager(self, keys, outerjoin, **kargs):
        """Helper method for applying join()/outerjoin() with contains_eager()
        """
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
        """Apply `self.join()` + `self.options(contains_eager())`."""
        return self._join_eager(keys, False, **kargs)

    def outerjoin_eager(self, *keys, **kargs):
        """Apply `self.outerjoin()` + `self.options(contains_eager())`."""
        return self._join_eager(keys, True, **kargs)

    def _join_load(self, keys, load_type, **kargs):
        """Helper method for returning load strategies."""
        opt = getattr(orm, load_type)(keys[0], **kargs)

        for k in keys[1:]:
            opt = getattr(opt, load_type)(k)

        return self.options(opt)

    def joinedload(self, *keys, **kargs):
        """Apply joinedload() to `keys`"""
        return self._join_load(keys, 'joinedload', **kargs)

    def immediateload(self, *keys, **kargs):
        """Apply immediateload() to `keys`"""
        return self._join_load(keys, 'immediateload', **kargs)

    def lazyload(self, *keys, **kargs):
        """Apply lazyload() to `keys`"""
        return self._join_load(keys, 'lazyload', **kargs)

    def noload(self, *keys, **kargs):
        """Apply noload() to `keys`"""
        return self._join_load(keys, 'noload', **kargs)

    def subqueryload(self, *keys, **kargs):
        """Apply subqueryload() to `keys`"""
        return self._join_load(keys, 'subqueryload', **kargs)

    def load_only(self, *columns):
        """Apply `load_only()` to query"""
        obj, columns = get_load_options(*columns)
        return self.options(obj.load_only(*columns))

    def defer(self, *columns):
        """Apply `defer()` to query"""
        obj, columns = get_load_options(*columns)
        opts = obj
        for column in columns:
            opts = opts.defer(column)
        return self.options(opts)

    def undefer(self, *columns):
        """Apply `undefer()` to query"""
        obj, columns = get_load_options(*columns)
        opts = obj
        for column in columns:
            opts = opts.undefer(column)
        return self.options(opts)

    def undefer_group(self, *names):
        """Apply `undefer_group()` to query"""
        obj, names = get_load_options(*names)
        return self.options(obj.undefer_group(names[0]))

    def map(self, func):
        """Call native `map` on `self.all()`"""
        return [func(item) for item in self.all()]

    def reduce(self, func, initial=None, reverse=False):
        """Reduce `self.all()` using `func`"""
        items = self.all()

        if reverse:
            items = reversed(items)

        result = initial
        for item in items:
            result = func(result, item)
        return result

    def reduce_right(self, func, initial=None):
        """Reduce reversed `self.all()` using `func`"""
        return self.reduce(func, initial=initial, reverse=True)

    def pluck(self, column):
        """Pluck `column` attribute values from `self.all()` results and return
        as list.
        """
        return [getattr(r, column, None) for r in self.all()]

    def page(self, page=1, per_page=None):
        """Return query with limit and offset applied for page"""
        if per_page is None:
            per_page = self.DEFAULT_PER_PAGE

        return self.limit(per_page).offset((page - 1) * per_page)

    def paginate(self, page=1, per_page=None, error_out=True):
        """Return Pagination instance using already defined query parameters"""
        if error_out and page < 1:
            raise IndexError

        if per_page is None:
            per_page = self.DEFAULT_PER_PAGE

        items = self.page(page, per_page).all()

        if not items and page != 1 and error_out:
            raise IndexError

        # No need to count if we're on the first page and there are fewer items
        # than we expected.
        if page == 1 and len(items) < per_page:
            total = len(items)
        else:
            total = self.order_by(None).count()

        return Pagination(self, page, per_page, total, items)


class QueryModel(Query):
    """Class used for default query property class. It's assumed that is how
    this class will be used so there may be cases where some of its functions
    won't work properly outside that context.
    """

    # All available search filter functions indexed by a canonical name which
    # will be referenced in advanced/simple search. All filter functions should
    # take a single value and return an SQLAlchemy filter expression.
    # I.e. {key: lambda value: Model.column_name.contains(value)}
    __search_filters__ = {}

    # Advanced search models search by named parameters. Generally found on
    # advanced search forms where each field maps to a specific database field
    # that will be queried against. If defined as a list, each item should be
    # a key from __search_filters__. The matching __search_filters__ function
    # will be used in the query. If defined as a dict, it should have the same
    # format as __search_filters__.
    __advanced_search__ = []

    # Simple search models search by phrase (like Google search). Defined like
    # __advanced_search__.
    __simple_search__ = []

    @property
    def Model(self):
        """Return primary entity model class."""
        return self.entities[0]

    def get_search_filters(self, keys):
        """Return __search_filters__ filtered by keys."""
        if isinstance(keys, dict):
            return keys
        else:
            return dict([(key, self.__search_filters__[key]) for key in keys])

    def advanced_filter(self, search_dict=None):
        """Return the compiled advanced search filter mapped to search_dict."""
        if search_dict is None:  # pragma: no cover
            search_dict = {}

        filter_funcs = self.get_search_filters(self.__advanced_search__)
        term_filters = [filter_funcs[key](value)
                        for key, value in iteritems(search_dict)
                        if key in filter_funcs]

        # All filters should match for an advanced search.
        return and_(*term_filters)

    def simple_filter(self, search_terms=None):
        """Return the compiled simple search filter mapped to search_terms."""
        if search_terms is None:  # pragma: no cover
            search_terms = []

        filter_funcs = self.get_search_filters(self.__simple_search__)

        # Only support AND'ing search terms together. Apply each simple search
        # filter to each search term and group them together.
        term_filters = [[func(term) for func in filter_funcs.values()]
                        for term in search_terms]

        # Each item in term_filters is a list of filters applied to one of
        # the search terms contained in search_string. We need at least one
        # simple filter to match for each term. We need all search terms to
        # have at least simple filter match.
        return and_(*[or_(*filters) for filters in term_filters])

    def search(self, search_string=None, search_dict=None,
               limit=None, offset=None, order_by=None):
        """Perform combination of simple/advanced searching with optional
        limit/offset support.
        """
        model_primary_keys = self.Model.primary_keys

        # Apply search filtering and pagination to Model's primary keys so we
        # can use the query as a subquery. In order to properly handle
        # pagination, we should use a subquery so that the outer level joins
        # won't cause records to be excluded when those includes *-to-many
        # relationships. For example, if we were returning a query of user +
        # user keywords (one-to-many), then for something like the first 25
        # users, we may actually have more than that many records since we're
        # joining on many records from the user keywords table.
        model_query = original = self.session.query(
            *model_primary_keys).distinct()

        if search_string is not None:
            model_query = model_query.filter(
                self.simple_filter(search_string.split()))

        if search_dict is not None:
            model_query = model_query.filter(
                self.advanced_filter(search_dict))

        if limit is not None:
            model_query = model_query.limit(limit)

        if offset is not None:
            model_query = model_query.offset(offset)

        if order_by is not None:
            model_query = model_query.order_by(order_by)

        if model_query != original:
            subquery = model_query.subquery()

            query = self.join(subquery, join_subquery_on_columns(
                subquery, model_primary_keys))
        else:
            query = self

        return query


class QueryProperty(object):
    """Query property accessor which gives a model access to query capabilities
    via Model.query which is equivalent to session.query(Model)
    """
    def __init__(self, session):
        self.session = session

    def __get__(self, model, Model):
        mapper = orm.class_mapper(Model)
        if mapper:
            if not getattr(Model, 'query_class', None):
                Model.query_class = QueryModel

            query_property = Model.query_class(mapper, session=self.session())

            return query_property


##
# Pagination class and usage adapated from Flask-SQLAlchemy:
# https://github.com/mitsuhiko/flask-sqlalchemy
##


class Pagination(object):
    """
    Internal helper class returned by `BaseQuery.paginate`.  You
    can also construct it from any other SQLAlchemy query object if you are
    working with other libraries.  Additionally it is possible to pass `None`
    as query object in which case the `prev` and `next` will
    no longer work.
    """

    def __init__(self, query, page, per_page, total, items):
        # the unlimited query object that was used to create this pagination
        # object
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
        if self.per_page == 0:
            self.pages = 0
        else:
            self.pages = int(ceil(self.total / float(self.per_page)))

        # number of the previous page
        self.prev_num = self.page - 1

        # True if a previous page exists
        self.has_prev = self.page > 1

        # number of the next page
        self.next_num = self.page + 1

        # True if a next page exists
        self.has_next = self.page < self.pages

    def prev(self, error_out=False):
        """Returns a `Pagination` object for the previous page."""
        assert self.query is not None, \
            'a query object is required for this method to work'
        return self.query.paginate(self.page - 1, self.per_page, error_out)

    def next(self, error_out=False):
        """Returns a `Pagination` object for the next page."""
        assert self.query is not None, \
            'a query object is required for this method to work'
        return self.query.paginate(self.page + 1, self.per_page, error_out)


def get_load_options(*columns):
    """Helper method that attempts to extract a sqlalchemy object from
    `columns[0]` and return remaining columns to apply to a query load method.
    """
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
