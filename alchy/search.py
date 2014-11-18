"""SQLAlchemy query filter factories usable in
:attr:`alchy.query.QueryModel.__search_filters__`.

These are factory functions that return common filter operations as functions
which are then assigned to the model class' search config attributes. These
functions are syntatic sugar to make it easier to define compatible search
functions. However, due to the fact that a model's query class has to be
defined before the model and given that the model column attributes need to be
defined before using the search factories, there are two ways to use the search
factories on the query class:

1. Define :attr:`alchy.query.QueryModel.__search_filters__` as a property \
that returns the filter dict.
2. Pass in a callable that returns the column.

For example, *without* :mod:`alchy.search` one would define a
:attr:`alchy.query.QueryModel.__search_filters__` similar to::

    class UserQuery(QueryModel):
        __search_filters = {
            'email': lambda value: User.email.like(value)
        }

    class User(Model):
        query_class = UserQuery
        email = Column(types.String(100))

Using :mod:`alchy.search` the above then becomes::

    class UserQuery(QueryModel):
        @property
        def __search_filters__(self):
            return {
                'email': like(User.email)
            }

    class User(Model):
        query_class = UserQuery
        email = Column(types.String(100))

Or if a callable is passed in::

    from alchy import search

    class UserQuery(QueryModel):
        __search_filters__ = {
            'email': like(lambda: User.email)
        }

    class User(Model):
        query_class = UserQuery
        email = Column(types.String(100))

The general naming convention for each comparator is:

- positive comparator: ``<base>`` (e.g. :func:`like`)
- negative comparator: ``not<base>`` (e.g. :func:`notlike`)

The basic call signature for the :mod:`search` functions is::

    # search.<function>(column)
    # e.g.
    search.contains(email)
"""
# pylint: disable=invalid-name

from sqlalchemy import not_


__all__ = [
    'like',
    'notlike',
    'ilike',
    'notilike',
    'startswith',
    'notstartswith',
    'endswith',
    'notendswith',
    'contains',
    'notcontains',
    'icontains',
    'noticontains',
    'in_',
    'notin_',
    'eq',
    'noteq',
    'gt',
    'notgt',
    'ge',
    'notge',
    'lt',
    'notlt',
    'le',
    'notle',
    'any_',
    'notany_',
    'has',
    'nothas',
    'eqenum',
    'noteqenum',
]


class ColumnOperator(object):
    """Base class for column operator based search factories."""
    op = None

    def __init__(self, column):
        self.column = column

    def compare(self, value):
        """Return comparision with value."""
        return getattr(self.column, self.op)(value)

    def __call__(self, value):
        """Makes comparision."""
        if hasattr(self.column, '__call__'):
            self.column = self.column()
        return self.compare(value)


class NegateOperator(ColumnOperator):
    """Negates a ColumnOperator class."""
    def __call__(self, value):
        return not_(super(NegateOperator, self).__call__(value))


class RelationshipOperator(ColumnOperator):
    """Base class for relationship operator based search factories."""
    def __init__(self, column, column_operator):
        self.column = column
        self.column_operator = column_operator

    def compare(self, value):
        """Return comparision with value."""
        return getattr(self.column, self.op)(self.column_operator(value))


class DeclarativeEnumOperator(ColumnOperator):
    """Base class for DeclarativeEnum operator based search factorires."""
    def __init__(self, column, enum_class):
        self.column = column
        self.enum_class = enum_class

    def compare(self, value):
        """Return comparision with value."""
        try:
            return self.column == self.enum_class.from_string(value)
        except ValueError:
            return None


class like(ColumnOperator):
    """Return ``like`` filter function using ORM column field."""
    op = 'like'


class notlike(like, NegateOperator):
    """Return ``not(like)`` filter function using ORM column field."""
    pass


class ilike(ColumnOperator):
    """Return ``ilike`` filter function using ORM column field."""
    op = 'ilike'


class notilike(ilike, NegateOperator):
    """Return ``not(ilike)`` filter function using ORM column field."""
    pass


class startswith(ColumnOperator):
    """Return ``startswith`` filter function using ORM column field."""
    op = 'startswith'


class notstartswith(startswith, NegateOperator):
    """Return ``not(startswith)`` filter function using ORM column field."""
    pass


class endswith(ColumnOperator):
    """Return ``endswith`` filter function using ORM column field."""
    op = 'endswith'


class notendswith(endswith, NegateOperator):
    """Return ``not(endswith)`` filter function using ORM column field."""
    pass


class contains(ColumnOperator):
    """Return ``contains`` filter function using ORM column field."""
    op = 'contains'


class notcontains(contains, NegateOperator):
    """Return ``not(contains)`` filter function using ORM column field."""
    pass


class icontains(ColumnOperator):
    """Return ``icontains`` filter function using ORM column field."""
    def compare(self, value):
        return self.column.ilike('%{0}%'.format(value))


class noticontains(icontains, NegateOperator):
    """Return ``not(icontains)`` filter function using ORM column field."""
    pass


class in_(ColumnOperator):
    """Return ``in_`` filter function using ORM column field."""
    op = 'in_'


class notin_(in_, NegateOperator):
    """Return ``not(in_)`` filter function using ORM column field."""
    pass


class eq(ColumnOperator):
    """Return ``==`` filter function using ORM column field."""
    def compare(self, value):
        return self.column == value


class noteq(eq, NegateOperator):
    """Return ``not(==)`` filter function using ORM column field."""
    pass


class gt(ColumnOperator):
    """Return ``>`` filter function using ORM column field."""
    def compare(self, value):
        return self.column > value


class notgt(gt, NegateOperator):
    """Return ``not(>)`` filter function using ORM column field."""
    pass


class ge(ColumnOperator):
    """Return ``>=`` filter function using ORM column field."""
    def compare(self, value):
        return self.column >= value


class notge(ge, NegateOperator):
    """Return ``not(>=)`` filter function using ORM column field."""
    pass


class lt(ColumnOperator):
    """Return ``<`` filter function using ORM column field."""
    def compare(self, value):
        return self.column < value


class notlt(lt, NegateOperator):
    """Return ``not(<)`` filter function using ORM column field."""
    pass


class le(ColumnOperator):
    """Return ``<=`` filter function using ORM column field."""
    def compare(self, value):
        return self.column <= value


class notle(le, NegateOperator):
    """Return ``not(<=)`` filter function using ORM column field."""
    pass


class any_(RelationshipOperator):
    """Return ``any`` filter function using ORM relationship field."""
    op = 'any'


class notany_(any_, NegateOperator):
    """Return ``not(any)`` filter function using ORM relationship field."""
    pass


class has(RelationshipOperator):
    """Return ``has`` filter function using ORM relationship field."""
    op = 'has'


class nothas(has, NegateOperator):
    """Return ``not(has)`` filter function using ORM relationship field."""
    pass


class eqenum(DeclarativeEnumOperator):
    """Return ``==`` filter function using ORM DeclarativeEnum field."""
    pass


class noteqenum(eqenum, NegateOperator):
    """Return ``not(==)`` filter function using ORM DeclarativeEnum field."""
    pass


class inenum(DeclarativeEnumOperator):
    """Return ``in_`` filter function using ORM DeclarativeEnum field."""
    def compare(self, value):
        """Return comparision with value."""
        if not isinstance(value, (tuple, list)):
            value = [value]

        try:
            return self.column.in_([self.enum_class.from_string(val)
                                    for val in value])
        except ValueError:
            return None


class notinenum(inenum, NegateOperator):
    """Return ``not(in_)`` filter function using ORM DeclarativeEnum field."""
    pass
