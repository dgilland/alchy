# pylint: disable=C0103
"""SQLAlchemy query filter factories usable in
alchy.QueryModel.__search_filter__.

These are factory functions that return common filter operations as functions
which are then assigned to the model class' search config attributes.

For example:

    class UserQuery(QueryModel):
        @property
        def __search_filters__(self):
            return {
                'email': like(User.email)
            }

    class User(Model):
        query_class = UserQuery
        email = Column(types.String(100))

without using the search function:

    class UserQuery(QueryModel):
        __search_filters = {
            'email': lambda value: User.email.like(value)
        }

    class User(Model):
        query_class = UserQuery
        email = Column(types.String(100))

The general naming convention for each comparator is:

- positive comparator: base (e.g. "like")
- negative comparator: notbase (e.g. "notlike")
"""

from sqlalchemy import not_


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


class like(ColumnOperator):
    """Return like filter function using ORM column field."""
    op = 'like'


class notlike(like, NegateOperator):
    """Return not like filter function using ORM column field."""
    pass


class ilike(ColumnOperator):
    """Return ilike filter function using ORM column field."""
    op = 'ilike'


class notilike(ilike, NegateOperator):
    """Return not ilike filter function using ORM column field."""
    pass


class startswith(ColumnOperator):
    """Return startswith filter function using ORM column field."""
    op = 'startswith'


class notstartswith(startswith, NegateOperator):
    """Return not startswith filter function using ORM column field."""
    pass


class endswith(ColumnOperator):
    """Return endswith filter function using ORM column field."""
    op = 'endswith'


class notendswith(endswith, NegateOperator):
    """Return not endswith filter function using ORM column field."""
    pass


class contains(ColumnOperator):
    """Return contains filter function using ORM column field."""
    op = 'contains'


class notcontains(contains, NegateOperator):
    """Return not contains filter function using ORM column field."""
    pass


class in_(ColumnOperator):
    """Return in_ filter function using ORM column field."""
    op = 'in_'


class notin_(in_, NegateOperator):
    """Return not in_ filter function using ORM column field."""
    pass


class eq(ColumnOperator):
    """Return == filter function using ORM column field."""
    def compare(self, value):
        return self.column == value


class noteq(eq, NegateOperator):
    """Return not(==) filter function using ORM column field."""
    pass


class gt(ColumnOperator):
    """Return > filter function using ORM column field."""
    def compare(self, value):
        return self.column > value


class notgt(gt, NegateOperator):
    """Return not(>) filter function using ORM column field."""
    pass


class ge(ColumnOperator):
    """Return >= filter function using ORM column field."""
    def compare(self, value):
        return self.column >= value


class notge(ge, NegateOperator):
    """Return not(>=) filter function using ORM column field."""
    pass


class lt(ColumnOperator):
    """Return < filter function using ORM column field."""
    def compare(self, value):
        return self.column < value


class notlt(lt, NegateOperator):
    """Return not(<) filter function using ORM column field."""
    pass


class le(ColumnOperator):
    """Return <= filter function using ORM column field."""
    def compare(self, value):
        return self.column <= value


class notle(le, NegateOperator):
    """Return not(<=) filter function using ORM column field."""
    pass


class any_(RelationshipOperator):
    """Return any filter function using ORM relationship field."""
    op = 'any'


class notany_(any_, NegateOperator):
    """Return not(any) filter function using ORM relationship field."""
    pass


class has(RelationshipOperator):
    """Return has filter function using ORM relationship field."""
    op = 'has'


class nothas(has, NegateOperator):
    """Return not(has) filter function using ORM relationship field."""
    pass
