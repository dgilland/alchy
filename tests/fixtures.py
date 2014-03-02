
from sqlalchemy import orm, types, Column, ForeignKey
from sqlalchemy.ext.hybrid import hybrid_property

from alchy import model, query
from alchy.types import DeclarativeEnum


Model = model.make_declarative_base()


class Foo(Model):
    __tablename__ = 'foo'

    _id             = Column(types.Integer(), primary_key=True)
    string          = Column(types.String())
    number          = Column(types.Integer())
    boolean         = Column(types.Boolean(), default=True)
    deferred1_col1  = orm.deferred(Column(types.Boolean()), group='deferred_1')
    deferred1_col2  = orm.deferred(Column(types.Boolean()), group='deferred_1')
    deferred2_col3  = orm.deferred(Column(types.Boolean()), group='deferred_2')
    deferred2_col4  = orm.deferred(Column(types.Boolean()), group='deferred_2')

    bars = orm.relationship('Bar', lazy=True)
    quxs = orm.relationship('Qux', lazy=True)

    __advanced_search__ = {
        'foo_string': lambda value: Foo.string.like('%{0}%'.format(value)),
        'foo_number': lambda value: Foo.number == value
    }

    __simple_search__ = {
        'foo_string': __advanced_search__['foo_string']
    }

    @orm.validates('number')
    def validate_number(self, key, value):
        if value < 0:
            raise ValueError('"number" must be positive')
        return value

    def view_joined(self):
        return self.query.options(
            orm.joinedload('bars').joinedload('bazs'),
            orm.joinedload('quxs')
        )


class Bar(Model):
    __tablename__ = 'bar'

    _id             = Column(types.Integer(), primary_key=True)
    string          = Column(types.String())
    number          = Column(types.Integer())
    foo_id          = Column(types.Integer(), ForeignKey('foo._id'))
    deferred1_col1  = orm.deferred(Column(types.Boolean()), group='bar_deferred_1')
    deferred2_col2  = orm.deferred(Column(types.Boolean()), group='bar_deferred_2')

    foo = orm.relationship('Foo')
    bazs = orm.relationship('Baz')

    __advanced_search__ = {
        'bar_string': lambda value: Bar.string.like('%{0}%'.format(value)),
        'bar_number': lambda value: Bar.number == value
    }

    __simple_search__ = {
        'bar_string': __advanced_search__['bar_string']
    }


class Baz(Model):
    __tablename__ = 'baz'

    _id         = Column(types.Integer(), primary_key=True)
    string      = Column(types.String())
    number      = Column(types.Integer())
    bar_id      = Column(types.Integer(), ForeignKey('bar._id'))

    bar = orm.relationship('Bar')

    @hybrid_property
    def hybrid_number(self):
        return self.number * self.number

    @hybrid_number.setter
    def hybrid_number(self, n):
        self.number = n / n


class Qux(Model):
    __tablename__ = 'qux'

    _id         = Column(types.Integer(), primary_key=True)
    string      = Column(types.String())
    number      = Column(types.Integer())
    foo_id      = Column(types.Integer(), ForeignKey('foo._id'))

    foo = orm.relationship('Foo')


class OrderStatus(DeclarativeEnum):
    pending     = ('p', 'Pending')
    submitted   = ('s', 'Submitted')
    complete    = ('c', 'Complete')


class Order(Model):
    __tablename__ = 'orders'
    _id         = Column(types.Integer(), primary_key=True)
    status      = Column(OrderStatus.db_type(), default=OrderStatus.pending)


class AutoGenTableName(Model):
    _id = Column(types.Integer(), primary_key=True)
    name = Column(types.String())


class MultiplePrimaryKey(Model):
    _id1 = Column(types.Integer(), primary_key=True)
    _id2 = Column(types.Integer(), primary_key=True)
    _id3 = Column(types.Integer(), primary_key=True)


Models = {
    'Foo': Foo,
    'Bar': Bar,
    'Baz': Baz,
    'Qux': Qux,
    'Order': Order
}

data = {
    'Foo': [
        {'_id': 1, 'string': 'Joe Smith', 'number': 3},
        {'_id': 2, 'string': 'Betty Boop', 'number': 5},
        {'_id': 3, 'string': 'Phil McKraken', 'number': 2},
        {'_id': 4, 'string': 'Bill Smith', 'number': 3},
        {'_id': 5, 'string': 'Jack Benimble', 'number': 7},
    ],
    'Bar': [
        {'_id': 1, 'string': 'Power Play', 'number': 1, 'foo_id': 1},
        {'_id': 2, 'string': 'Bob Smith', 'number': 7, 'foo_id': 1},
        {'_id': 3, 'string': 'Arthur Clarke', 'number': 9, 'foo_id': 2},
        {'_id': 4, 'string': 'Robert Heinlein', 'number': 10},
    ],
    'Baz': [
        {'_id': 1, 'string': 'Elroy Jenkins', 'number': 3, 'bar_id': 3},
        {'_id': 2, 'string': 'John Smith', 'number': 4, 'bar_id': 1},
        {'_id': 3, 'string': 'Isaac Asimov', 'number': 8, 'bar_id': 2},
    ],
    'Qux': [
        {'_id': 1, 'string': 'Foo Bar', 'number': 2, 'foo_id': 1},
        {'_id': 2, 'string': 'Axel Rose', 'number': 6, 'foo_id': 1},
        {'_id': 3, 'string': 'Zoom', 'number': 1, 'foo_id': 2},
    ],
    'Order': [
        {'_id': 1, 'status': OrderStatus.submitted}
    ]
}
