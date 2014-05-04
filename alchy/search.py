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

without using the factory function:

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


def negate(base_func):
    """Factory negate function generator."""
    def _negate(*args, **kargs):
        """Negating function generator"""
        def _base_func(*_args, **_kargs):
            """Negating function"""
            return not_(base_func(*args, **kargs)(*_args, **_kargs))
        return _base_func
    return _negate


def like(column):
    """Return like filter function using ORM column field."""
    def _like(value):
        """Return like filter."""
        return column.like(value)
    return _like

notlike = negate(like)


def ilike(column):
    """Return ilike filter function using ORM column field."""
    def _ilike(value):
        """Return ilike filter."""
        return column.ilike(value)
    return _ilike

notilike = negate(ilike)


def startswith(column):
    """Return startswith filter function using ORM column field."""
    def _startswith(value):
        """Return startswith filter."""
        return column.startswith(value)
    return _startswith

notstartswith = negate(startswith)


def endswith(column):
    """Return endswith filter function using ORM column field."""
    def _endswith(value):
        """Return endswith filter."""
        return column.endswith(value)
    return _endswith

notendswith = negate(endswith)


def contains(column):
    """Return contain filter function using ORM column field."""
    def _contains(value):
        """Return contains filter."""
        return column.contains(value)
    return _contains

notcontains = negate(contains)


def in_(column):
    """Return in filter function using ORM column field."""
    def _in_(value):
        """Return in filter."""
        return column.in_(value)
    return _in_

notin_ = negate(in_)


def eq(column):
    """Return == filter function using ORM column field."""
    def _eq(value):
        """Return == filter."""
        return column == value
    return _eq

noteq = negate(eq)


def gt(column):
    """Return > filter function using ORM column field."""
    def _gt(value):
        """Return > filter."""
        return column > value
    return _gt

notgt = negate(gt)


def ge(column):
    """Return >= filter function using ORM column field."""
    def _ge(value):
        """Return >= filter."""
        return column >= value
    return _ge

notge = negate(ge)


def lt(column):
    """Return < filter function using ORM column field."""
    def _lt(value):
        """Return < filter."""
        return column < value
    return _lt

notlt = negate(lt)


def le(column):
    """Return <= filter function using ORM column field."""
    def _le(value):
        """Return <= filter."""
        return column <= value
    return _le

notle = negate(le)
