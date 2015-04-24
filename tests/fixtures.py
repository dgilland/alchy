
from sqlalchemy import orm, types, Column, ForeignKey, Index
from sqlalchemy.ext.declarative import ConcreteBase, AbstractConcreteBase
from sqlalchemy.ext.hybrid import hybrid_property

from alchy import model, query
from alchy.types import DeclarativeEnum


Model = model.make_declarative_base()


class FooQuery(query.QueryModel):
    __search_filters__ = {
        'foo_string': lambda value: Foo.string.contains(value),
        'foo_string2': lambda value: Foo.string2.contains(value),
        'foo_number': lambda value: Foo.number == value,
        'bar_string': lambda value: Foo.bars.any(Bar.string.contains(value))
    }

    __advanced_search__ = ['foo_string', 'foo_string2', 'foo_number']
    __simple_search__ = ['foo_string', 'foo_string2', 'bar_string']


class Foo(Model):
    __tablename__ = 'foo'
    query_class = FooQuery

    _id = Column(types.Integer(), primary_key=True)
    string = Column(types.String())
    string2 = Column(types.String())
    number = Column(types.Integer())
    boolean = Column(types.Boolean(), default=True)
    deferred1_col1 = orm.deferred(Column(types.Boolean()), group='deferred_1')
    deferred1_col2 = orm.deferred(Column(types.Boolean()), group='deferred_1')
    deferred2_col3 = orm.deferred(Column(types.Boolean()), group='deferred_2')
    deferred2_col4 = orm.deferred(Column(types.Boolean()), group='deferred_2')

    bars = orm.relationship('Bar', lazy=True)
    quxs = orm.relationship('Qux', lazy=True)

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


class BarQuery(query.QueryModel):
    __advanced_search__ = {
        'bar_string': lambda value: Bar.string.contains(value),
        'bar_number': lambda value: Bar.number == value
    }

    __simple_search__ = {
        'bar_string': lambda value: Bar.string.contains(value)
    }


class Bar(Model):
    __tablename__ = 'bar'
    query_class = BarQuery

    _id = Column(types.Integer(), primary_key=True)
    string = Column(types.String())
    number = Column(types.Integer())
    foo_id = Column(types.Integer(), ForeignKey('foo._id'))
    deferred1_col1 = orm.deferred(
        Column(types.Boolean()), group='bar_deferred_1')
    deferred2_col2 = orm.deferred(
        Column(types.Boolean()), group='bar_deferred_2')

    foo = orm.relationship('Foo')
    bazs = orm.relationship('Baz')


class Baz(Model):
    __tablename__ = 'baz'

    _id = Column(types.Integer(), primary_key=True)
    string = Column(types.String())
    number = Column(types.Integer())
    bar_id = Column(types.Integer(), ForeignKey('bar._id'))

    bar = orm.relationship('Bar')

    @hybrid_property
    def hybrid_number(self):
        return self.number * self.number

    @hybrid_number.setter
    def hybrid_number(self, n):
        self.number = n / n


class Qux(Model):
    __tablename__ = 'qux'

    _id = Column(types.Integer(), primary_key=True)
    string = Column(types.String())
    number = Column(types.Integer())
    foo_id = Column(types.Integer(), ForeignKey('foo._id'))

    foo = orm.relationship('Foo')
    doz = orm.relationship('Doz', uselist=False)


class Doz(Model):
    qux_id = Column(types.Integer(), ForeignKey('qux._id'), primary_key=True)
    name = Column(types.String())


class OrderStatus(DeclarativeEnum):
    pending = ('p', 'Pending')
    submitted = ('s', 'Submitted')
    complete = ('c', 'Complete')


class OrderSide(DeclarativeEnum):
    buy = ('b', 'Buy')
    sell = ('s', 'Sell')
    __enum_args__ = {'name': 'ck_order_side_constraint',
                     'inherit_schema': True}


class Order(Model):
    __tablename__ = 'orders'
    _id = Column(types.Integer(), primary_key=True)
    status = Column(OrderStatus.db_type(), default=OrderStatus.pending)
    side = Column(OrderSide.db_type(), default=OrderSide.buy)


class AutoGenTableName(Model):
    _id = Column(types.Integer(), primary_key=True)
    name = Column(types.String())


class BaseAutoGen(object):
    _id = Column(types.Integer(), primary_key=True)


class InheritedAutoGenTableName(Model, BaseAutoGen):
    name = Column(types.String())


class MultiplePrimaryKey(Model):
    _id1 = Column(types.Integer(), primary_key=True)
    _id2 = Column(types.Integer(), primary_key=True)
    _id3 = Column(types.Integer(), primary_key=True)


class A(Model):
    _id = Column(types.Integer(), primary_key=True)
    a_c = orm.relationship('AC', lazy=False)

    @property
    def c(self):
        return dict([(a_c.key, a_c.c) for a_c in self.a_c])

    @property
    def __to_dict__(self):
        return set(['_id', 'c'])


class AC(Model):
    a_id = Column(types.Integer(), ForeignKey('a._id'), primary_key=True)
    c_id = Column(types.Integer(), ForeignKey('c._id'), primary_key=True)
    key = Column(types.String())

    c = orm.relationship('C', lazy=False)


class C(Model):
    _id = Column(types.Integer(), primary_key=True)


class Search(Model):
    _id = Column(types.Integer(), primary_key=True)
    string = Column(types.String())
    search_one_id = Column(types.Integer(), ForeignKey('search_one._id'))
    status = Column(OrderStatus.db_type(name='ck_order_status_check_name'),
                    default=OrderStatus.pending)

    many = orm.relationship('SearchMany')
    one = orm.relationship('SearchOne')


class SearchOne(Model):
    _id = Column(types.Integer(), primary_key=True)
    string = Column(types.String())


class SearchMany(Model):
    _id = Column(types.Integer(), primary_key=True)
    string = Column(types.String())
    search_id = Column(types.Integer(), ForeignKey('search._id'))


# Classes to test inheritance

class AAA(Model):
    __abstract__ = True
    idx = Column(types.Integer(), primary_key=True)


class BBB(AAA):
    __abstract__ = True
    b_int = Column(types.Integer())


class CCC(BBB):
    c_int = Column(types.Integer())


def get_CCC2():
    class CCC2(BBB):
        idx = Column(types.Integer(), primary_key=False)
        c2_int = Column(types.Integer())

    return CCC2


class DDD(CCC):
    idx = Column(types.Integer(), ForeignKey(CCC.idx),
                 primary_key=True)
    d_int = Column(types.Integer())


class EEE(BBB):
    idx = Column(types.Integer(), primary_key=True)
    e_str = Column(types.String())
    __global_mapper_args__ = {'polymorphic_on': e_str}


class FFF(EEE):
    f_int = Column(types.Integer())
    __local_mapper_args__ = {'polymorphic_identity': 'eee_subtype_fff'}


class FFF2(EEE):
    f2_int = Column(types.Integer())
    __mapper_args__ = {'polymorphic_identity': 'eee_subtype_fff2'}


# Concrete table inheritance
class GGG(CCC):
    idx = Column(types.Integer(), primary_key=True)
    g_int = Column(types.Integer())
    __local_mapper_args__ = {'concrete': True}


# Concrete table inheritance - using ConcreteBase
class HHH(ConcreteBase, BBB):
    h_int = Column(types.Integer())
    __local_mapper_args__ = {'polymorphic_on': h_int, 'concrete': True}


class III(HHH):
    idx = Column(types.Integer(), primary_key=True)
    i_int = Column(types.Integer())
    __mapper_args__ = {'polymorphic_identity': 2, 'concrete': True}


# Concrete table inheritance - using AbstractConcreteBase
class JJJ(AbstractConcreteBase, Model):
    idx = Column(types.Integer(), primary_key=True)
    j_int = Column(types.Integer())
    __local_mapper_args__ = {'polymorphic_on': j_int}


class KKK(JJJ):
    idx = Column(types.Integer(), primary_key=True)
    k_int = Column(types.Integer())
    __mapper_args__ = {'polymorphic_identity': 2, 'concrete': True}


class LLL(AbstractConcreteBase, Model):
    l_int = Column(types.Integer())
    __local_mapper_args__ = {'polymorphic_on': l_int}


class MMM(LLL):
    idx = Column(types.Integer(), primary_key=True)
    m_int = Column(types.Integer())
    __mapper_args__ = {'polymorphic_identity': 3, 'concrete': True}


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
