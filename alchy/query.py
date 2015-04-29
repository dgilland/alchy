"""Query subclass used by Manager as default session query class.
"""

from math import ceil

from sqlalchemy import orm, and_, or_, inspect
from sqlalchemy.orm.strategy_options import Load
from pydash import py_

from ._compat import iteritems


__all__ = [
    'Query',
    'QueryModel',
    'QueryProperty',
    'Pagination',
    'LoadOption'
]


class Query(orm.Query):
    """Extension of default Query class used in SQLAlchemy session queries.
    """

    #: Default per_page argument for pagination when per_page not specified.
    DEFAULT_PER_PAGE = 50

    @property
    def entities(self):
        """Return list of entity classes present in query."""
        return [e.mapper.class_ for e in self._entities]

    @property
    def join_entities(self):
        """Return list of the joined entity classes present in query."""
        return [e.mapper.class_ for e in self._join_entities]

    @property
    def all_entities(self):
        """Return list of entities + join_entities present in query."""
        return self.entities + self.join_entities

    def _join_eager(self, keys, use_outerjoin, **kargs):
        """Helper method for applying ``join()``/``outerjoin()` with
        ``contains_eager()``.
        """
        alias = kargs.pop('alias', {})
        options = kargs.pop('options', None)

        if not isinstance(alias, dict):
            alias = {keys[0]: alias}

        join_args = [(alias.get(key), key) for key in keys]

        load = orm.contains_eager(keys[0], alias=alias.get(keys[0]))

        for key in keys[1:]:
            load = load.contains_eager(key, alias=alias.get(key))

        if options:
            apply_load_options(load, options)

        join = self.outerjoin if use_outerjoin else self.join

        return join(*join_args).options(load)

    def join_eager(self, *keys, **kargs):
        """Apply ``join`` + ``self.options(contains_eager())``.

        Args:
            keys (mixed): Either string or column references to join
                path(s).

        Keyword Args:
            alias: Join alias or ``dict`` mapping key names to aliases.
            options (list): A list of :class:`LoadOption` to apply to the
                overall load strategy, i.e., each :class:`LoadOption` will be
                chained at the end of the load.
        """
        return self._join_eager(keys, False, **kargs)

    def outerjoin_eager(self, *keys, **kargs):
        """Apply ``outerjoin`` + ``self.options(contains_eager())``.

        Args:
            keys (mixed): Either string keys or column references to join
                path(s).

        Keyword Args:
            alias: Join alias or ``dict`` mapping key names to aliases.
            options (list): A list of :class:`LoadOption` to apply to the
                overall load strategy, i.e., each :class:`LoadOption` will be
                chained at the end of the load.
        """
        return self._join_eager(keys, True, **kargs)

    def _join_load(self, keys, load_strategy, **kargs):
        """Helper method for returning load strategies."""
        options = kargs.pop('options', None)

        load = getattr(orm, load_strategy)(keys[0], **kargs)

        for key in keys[1:]:
            load = getattr(load, load_strategy)(key)

        if options:
            load = apply_load_options(load, options)

        return self.options(load)

    def joinedload(self, *keys, **kargs):
        """Apply ``joinedload()`` to `keys`.

        Args:
            keys (mixed): Either string or column references to join
                path(s).

        Keyword Args:
            options (list): A list of :class:`LoadOption` to apply to the
                overall load strategy, i.e., each :class:`LoadOption` will be
                chained at the end of the load.

        Note:
            Additional keyword args will be passed to initial load creation.
        """
        return self._join_load(keys, 'joinedload', **kargs)

    def immediateload(self, *keys, **kargs):
        """Apply ``immediateload()`` to `keys`.

        Args:
            keys (mixed): Either string or column references to join
                path(s).

        Keyword Args:
            options (list): A list of :class:`LoadOption` to apply to the
                overall load strategy, i.e., each :class:`LoadOption` will be
                chained at the end of the load.

        Note:
            Additional keyword args will be passed to initial load creation.
        """
        return self._join_load(keys, 'immediateload', **kargs)

    def lazyload(self, *keys, **kargs):
        """Apply ``lazyload()`` to `keys`.

        Args:
            keys (mixed): Either string or column references to join
                path(s).

        Keyword Args:
            options (list): A list of :class:`LoadOption` to apply to the
                overall load strategy, i.e., each :class:`LoadOption` will be
                chained at the end of the load.

        Note:
            Additional keyword args will be passed to initial load creation.
        """
        return self._join_load(keys, 'lazyload', **kargs)

    def noload(self, *keys, **kargs):
        """Apply ``noload()`` to `keys`.

        Args:
            keys (mixed): Either string or column references to join
                path(s).

        Keyword Args:
            options (list): A list of :class:`LoadOption` to apply to the
                overall load strategy, i.e., each :class:`LoadOption` will be
                chained at the end of the load.

        Note:
            Additional keyword args will be passed to initial load creation.
        """
        return self._join_load(keys, 'noload', **kargs)

    def subqueryload(self, *keys, **kargs):
        """Apply ``subqueryload()`` to `keys`.

        Args:
            keys (mixed): Either string or column references to join
                path(s).

        Keyword Args:
            options (list): A list of :class:`LoadOption` to apply to the
                overall load strategy, i.e., each :class:`LoadOption` will be
                chained at the end of the load.

        Note:
            Additional keyword args will be passed to initial load creation.
        """
        return self._join_load(keys, 'subqueryload', **kargs)

    def load_only(self, *columns):
        """Apply ``load_only()`` to query."""
        obj, columns = get_load_options(*columns)
        return self.options(obj.load_only(*columns))

    def defer(self, *columns):
        """Apply ``defer()`` to query."""
        load, columns = get_load_options(*columns)
        for column in columns:
            load = load.defer(column)
        return self.options(load)

    def undefer(self, *columns):
        """Apply ``undefer()`` to query."""
        load, columns = get_load_options(*columns)
        for column in columns:
            load = load.undefer(column)
        return self.options(load)

    def undefer_group(self, *names):
        """Apply ``undefer_group()`` to query."""
        obj, names = get_load_options(*names)
        return self.options(obj.undefer_group(names[0]))

    def chain(self):
        """Return pydash chaining instance with items returned by
        :meth:`all`.

        See Also:
            `pydash's <http://pydash.readthedocs.org/>`_ documentation on
            `chaining <http://pydash.readthedocs.org/en/latest/chaining.html>`_
        """
        return py_.chain(self.all())

    def index_by(self, callback=None):
        """Index items returned by :meth:`all` using `callback`."""
        return py_.index_by(self.all(), callback)

    def map(self, callback=None):
        """Map `callback` to each item returned by :meth:`all`."""
        return py_.map(self.all(), callback)

    def reduce(self, callback=None, initial=None):
        """Reduce :meth:`all` using `callback`."""
        return py_.reduce(self.all(), callback, initial)

    def reduce_right(self, callback=None, initial=None):
        """Reduce reversed :meth:`all` using `callback`."""
        return py_.reduce_right(self.all(), callback, initial)

    def pluck(self, column):
        """Pluck `column` attribute values from :meth:`all` results and
        return as list.
        """
        return py_.pluck(self.all(), column)

    def page(self, page=1, per_page=None):
        """Return query with limit and offset applied for page."""
        if per_page is None:
            per_page = self.DEFAULT_PER_PAGE

        return self.limit(per_page).offset((page - 1) * per_page)

    def paginate(self, page=1, per_page=None, error_out=True):
        """Return :class:`Pagination` instance using already defined query
        parameters.
        """
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
    """Class used for default query property class for ``mymanager.query``,
    ``mymanager.session.query``, and ``MyModel.query``. Can be used in other
    libraries/implementations when creating a session::

        from sqlalchemy import orm

        from alchy import QueryModel
        # or if not using as query property
        # from alchy import Query


        session = orm.scoped_session(orm.sessionmaker())
        session.configure(query_cls=QueryModel)

    **NOTE:** If you don't plan to use the query class as a query property,
    then you can use the :class:`Query` class instead since it won't include
    features that only work within a query property context.

    Attributes:

        __search_filters__: All available search filter functions indexed by a
            canonical name which will be referenced in advanced/simple search.
            All filter functions should take a single value and return an
            SQLAlchemy filter expression, i.e.,
            ``{key: lambda value: Model.column_name.contains(value)}``

        __advanced_search__: Advanced search models search by named parameters.
            Generally found on advanced search forms where each field maps to a
            specific database field that will be queried against. If defined as
            a list, each item should be a key from :attr:`__search_filters__`.
            The matching :attr:`__search_filters__` function will be used in
            the query. If defined as a dict, it should have the same format as
            :attr:`__search_filters__`.

        __simple_search__: Simple search models search by phrase (like Google
            search). Defined like :attr:`__advanced_search__`.

        __order_by__: Default order-by to use when
            :attr:`alchy.model.ModelBase.query` used.
    """

    __search_filters__ = {}
    __advanced_search__ = []
    __simple_search__ = []
    __order_by__ = None

    @property
    def Model(self):
        """Return primary entity model class."""
        return self.entities[0]

    def get_search_filters(self, keys):
        """Return :attr:`__search_filters__` filtered by keys."""
        if isinstance(keys, dict):
            return keys
        else:
            return dict([(key, self.__search_filters__[key]) for key in keys])

    def advanced_filter(self, search_dict=None):
        """Return the compiled advanced search filter mapped to `search_dict`.
        """
        if search_dict is None:  # pragma: no cover
            search_dict = {}

        filter_funcs = self.get_search_filters(self.__advanced_search__)
        term_filters = [filter_funcs[key](value)
                        for key, value in iteritems(search_dict)
                        if key in filter_funcs]

        # All filters should match for an advanced search.
        return and_(*term_filters)

    def simple_filter(self, search_terms=None):
        """Return the compiled simple search filter mapped to `search_terms`.
        """
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

    def search(self, search_string=None, search_dict=None, **search_options):
        """Perform combination of simple/advanced searching with optional
        limit/offset support.
        """
        search_options.setdefault('limit', None)
        search_options.setdefault('offset', None)
        search_options.setdefault('order_by', self.__order_by__)

        query = self

        # Apply search filtering and pagination to Model's primary keys so we
        # can use the query as a subquery. In order to properly handle
        # pagination, we can use a subquery so that the outer level joins
        # won't cause records to be excluded when they include *-to-many
        # relationships. For example, if we were returning a query of user +
        # user keywords (one-to-many), then for something like the first 25
        # users, we may actually have more than that many records since we're
        # joining on many records from the user keywords table.
        original = (self.lazyload('*')
                    .load_only(*self.Model.primary_attrs())
                    .distinct())

        # Use the original query so that we preserve joins and where
        # statements.
        model_query = original

        if self.whereclause is not None:
            # If our base query contains a whereclause, then we need to
            # compelete the "transfer" of the base query's where statements to
            # model_query by wiping out the base query's criterion. i.e. We
            # only want to maintain selects and froms in the base query and
            # keep wheres in the model_query.

            # Call a generative query method that won't modify its state. This
            # is basically a no-op used to copy the query object and modify it
            # below. NOTE: There may be a better way to do this.
            query = query.filter()

            # Remove existing filters since they were transferred to the
            # model_query. This may seem kind of hacky but I don't know of a
            # better way to nullify the query object's where clause.
            query._criterion = None

        if search_string is not None:
            model_query = model_query.filter(
                self.simple_filter(search_string.split()))

        if search_dict is not None:
            model_query = model_query.filter(
                self.advanced_filter(search_dict))

        if search_options['order_by'] is not None:
            if not isinstance(search_options['order_by'], (list, tuple)):
                search_options['order_by'] = [search_options['order_by']]
            model_query = model_query.order_by(*search_options['order_by'])

        if search_options['limit'] is not None:
            model_query = model_query.limit(search_options['limit'])

        if search_options['offset'] is not None:
            model_query = model_query.offset(search_options['offset'])

        if model_query != original:
            subquery = model_query.subquery()
            query = query.join(
                subquery, join_subquery_on_columns(subquery,
                                                   self.Model.primary_keys()))

        return query


class QueryProperty(object):
    """Query property accessor which gives a model access to query capabilities
    via :attr:`alchy.model.ModelBase.query` which is equivalent to
    ``session.query(Model)``.
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
    """Internal helper class returned by :meth:`Query.paginate`. You can also
    construct it from any other SQLAlchemy query object if you are working with
    other libraries. Additionally it is possible to pass ``None`` as query
    object in which case the `prev` and `next` will no longer work.
    """

    def __init__(self, query, page, per_page, total, items):
        #: The query object that was used to create this pagination object.
        self.query = query

        #: The current page number (1 indexed).
        self.page = page

        #: The number of items to be displayed on a page.
        self.per_page = per_page

        #: The total number of items matching the query.
        self.total = total

        #: The items for the current page.
        self.items = items

        if self.per_page == 0:
            self.pages = 0
        else:
            #: The total number of pages.
            self.pages = int(ceil(self.total / float(self.per_page)))

        #: Number of the previous page.
        self.prev_num = self.page - 1

        #: True if a previous page exists.
        self.has_prev = self.page > 1

        #: Number of the next page.
        self.next_num = self.page + 1

        #: True if a next page exists.
        self.has_next = self.page < self.pages

    def prev(self, error_out=False):
        """Returns a :class:`Pagination` object for the previous page."""
        assert self.query is not None, \
            'a query object is required for this method to work'
        return self.query.paginate(self.page - 1, self.per_page, error_out)

    def next(self, error_out=False):
        """Returns a :class:`Pagination` object for the next page."""
        assert self.query is not None, \
            'a query object is required for this method to work'
        return self.query.paginate(self.page + 1, self.per_page, error_out)


class LoadOption(object):
    """Chained load option to apply to a load strategy when calling
    :class:`Query` load methods.

    Example usage: ::

        qry = (db.session.query(Product)
               .join_eager('category',
                           options=[LoadOption('noload', 'images')]))

    This would result in the ``noload`` option being chained to the eager
    option for ``Product.category`` and is equilvalent to: ::

        qry = (db.session.query(Product)
               .join('category')
               .options(contains_eager('category').noload('images')))
    """
    def __init__(self, strategy, *args, **kargs):
        self.strategy = strategy
        self.args = args
        self.kargs = kargs


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


def apply_load_options(load, options):
    """Apply load `options` to base `load` object.
    """
    for load_option in options:
        load = getattr(load, load_option.strategy)(*load_option.args,
                                                   **load_option.kargs)

    return load


def base_columns_from_subquery(subquery):
    """Return non-aliased, base columns from subquery."""
    # base_columns is a set so we need to cast to list.
    return [(column, list(column.base_columns))
            for column in subquery.c.values()]


def join_subquery_on_columns(subquery, columns):
    """Return join-on condition which maps subquery's columns to columns."""
    subquery_base_columns = base_columns_from_subquery(subquery)

    join_on = []
    for subquery_column, base_columns in subquery_base_columns:
        # Don't support joining to subquery column with more than 1 base
        # column.
        if len(base_columns) == 1 and base_columns[0] in columns:
            join_on.append(subquery_column == base_columns[0])

    if join_on:
        return and_(*join_on)
    else:  # pragma: no cover
        return None
