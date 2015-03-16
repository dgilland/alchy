
import sqlalchemy
from sqlalchemy import orm, Column, types, inspect, Index
from sqlalchemy.orm.exc import UnmappedClassError

from alchy import model, query, manager, events

from .base import TestQueryBase
from . import fixtures
from .fixtures import (
    Foo,
    Bar,
    Baz,
    Qux,
    AutoGenTableName,
    InheritedAutoGenTableName,
    MultiplePrimaryKey,
    Model
)


class TestModel(TestQueryBase):

    records = {
        'Foo': [{
            '_id': 100,
            'string': 'foo',
            'number': 3,
            'boolean': False,
            'ignored_field': 'bar'
        }]
    }

    def assertRecordValid(self, record, data):
        self.assertEqual(record._id, data['_id'])
        self.assertEqual(record.string, data['string'])
        self.assertEqual(record.number, data['number'])
        self.assertEqual(record.boolean, data['boolean'])

        self.assertFalse(hasattr(record, 'ignored_field'))

    def assertIsSubset(self, subset, superset):
        self.assertTrue(
            all(item in superset.items() for item in subset.items()))

    def assertIsNotSubset(self, subset, superset):
        self.assertRaises(
            AssertionError, self.assertIsSubset, subset, superset)

    def test_update(self):
        data = self.records['Foo'][0]

        record = Foo()

        # it should accept a dict
        record.update(data)
        self.assertRecordValid(record, data)

        record = Foo()

        # it should accept keyword args
        record.update(**data)
        self.assertRecordValid(record, data)

        # it should be used by __init__
        self.assertRecordValid(Foo(data), data)
        self.assertRecordValid(Foo(**data), data)

    def test_update_nested(self):
        bar = Bar.get(1)
        test = {'foo': {'string': 'BAR'}}

        bar.update(test)
        self.db.commit()
        foo = Foo.get(bar.foo_id)

        self.assertEqual(foo.string, test['foo']['string'])

    def test_update_null_relationship_with_empty_dict(self):
        bar = Bar.get(4)

        self.assertIsNone(bar.foo)

        test = {'foo': {}}

        bar.update(test)
        self.db.commit()

        self.assertIsNone(bar.foo)

    def test_update_relationship_with_list(self):
        bar = Bar.get(1)

        test = {'bazs': [{'string': 'BAZ0'}, {'string': 'BAZ1'}]}

        bar.update(test)
        self.db.commit()

        self.assertEqual(len(bar.bazs), len(test['bazs']))
        self.assertEqual(bar.bazs[0]['string'], test['bazs'][0]['string'])
        self.assertEqual(bar.bazs[1]['string'], test['bazs'][1]['string'])

    def test_update_relationship_with_dict(self):
        qux = Qux.get(1)

        test = {'doz': {'name': 'dozzer'}}

        qux.update(test)
        self.db.commit()

        self.assertEqual(qux.doz.name, test['doz']['name'])

    def test_query_property(self):
        self.assertIsInstance(Foo.query, query.Query)
        self.assertEqual(
            self.db.query(Foo).filter_by(number=3).all(),
            Foo.query.filter_by(number=3).all())

    def test_query_class_missing_default(self):
        """Test that models defined with query_class=None have default Query
        class for query_property.
        """
        class TestModel(Model):
            __tablename__ = 'test'
            _id = Column(types.Integer(), primary_key=True)

            query_class = None

        self.db.create_all()

        self.db.add_commit(TestModel(), TestModel())

        records = self.db.query(TestModel).all()

        self.assertTrue(len(records) > 0)
        self.assertEqual(
            TestModel.query.all(),
            records,
            "Model query property should return same results as session query"
        )
        self.assertIsInstance(
            TestModel.query,
            query.Query,
            "Model query property should be an instance of query.Query"
        )

    def test_query_property_with_unmapped(self):
        class Unmapped(object):
            qry = query.QueryProperty(None)

        self.assertRaises(UnmappedClassError, lambda: Unmapped.qry)

    def test_to_dict_with_lazy(self):
        data = fixtures.data['Foo'][0]
        record = self.db.query(Foo).get(data['_id'])

        as_dict = record.to_dict()

        # it should use default loading which is lazy
        self.assertIsSubset(data, as_dict)
        self.assertEqual(
            set(as_dict.keys()),
            set(['_id', 'string', 'string2', 'number', 'boolean']))

    def test_to_dict_with_joined(self):
        data = fixtures.data['Foo'][0]
        record = self.db.query(Foo).options(
            orm.joinedload('bars').joinedload('bazs'),
            orm.joinedload('quxs')
        ).get(data['_id'])

        as_dict = record.to_dict()

        # it should load relationships
        self.assertIsSubset(data, as_dict)
        self.assertEqual(
            set(as_dict.keys()),
            set(['_id', 'string', 'string2',
                 'number', 'boolean', 'quxs', 'bars']))

        # and relationship's relationships
        self.assertIn('bazs', as_dict['bars'][0])

    def test_to_dict_after_commit(self):
        record = Foo()
        self.assertEqual(record.to_dict(), {})

        self.db.add_commit(record)

        self.assertNotEqual(record.to_dict(), {})

    def test_dict_to_dict(self):
        data = Foo.get(1)

        self.assertEqual(dict(data), data.to_dict())

    def test_to_dict_hook(self):
        foo = Foo.get(1)

        def bar_to_dict():
            return [i for i, bar in enumerate(foo.bars)]

        foo.bars.to_dict = bar_to_dict
        data = foo.to_dict()
        self.assertEqual(data['bars'], bar_to_dict())

    def test_to_dict_with_field_as_dict(self):
        a = fixtures.A(a_c=[
            fixtures.AC(key='one', c=fixtures.C()),
            fixtures.AC(key='two', c=fixtures.C())
        ])

        self.db.add_commit(a)

        expected = {
            '_id': 1,
            'c': {
                'one': {'_id': 1},
                'two': {'_id': 2}
            }
        }

        self.assertEqual(a.to_dict(), expected)

    def test_to_dict_empty_nonlist_relationship(self):
        bar = Bar(foo=None)

        data = bar.to_dict()

        self.assertEqual(data['foo'], {})

    def test_attrs(self):
        baz = Baz.get(1)

        # it should be a class and instance property
        self.assertEqual(Baz.attrs(), baz.attrs())
        self.assertEqual(set(Baz.attrs()),
                         set(['_id', 'string', 'number', 'bar_id', 'bar']))

    def test_getitem(self):
        baz = Baz.get(1)

        self.assertEqual(baz.string, baz['string'])

    def test_setitem(self):
        baz = Baz.get(1)

        baz['string'] = baz.string * 2
        self.assertEqual(baz.string, baz['string'])

    def test_columns(self):
        baz = Baz.get(1)

        # it should be a class and instance property
        self.assertEqual(Baz.columns(), baz.columns())
        self.assertEqual(set(Baz.columns()),
                         set(['_id', 'string', 'number', 'bar_id']))

    def test_column_attrs(self):
        baz = Baz.get(1)

        # it should be a class and instance property
        self.assertEqual(Baz.column_attrs(), baz.column_attrs())
        self.assertEqual(set(Baz.column_attrs()),
                         set([Baz._id.property,
                              Baz.string.property,
                              Baz.number.property,
                              Baz.bar_id.property]))

    def test_descriptors(self):
        baz = Baz.get(1)

        # it should be a class and instance property
        self.assertEqual(Baz.descriptors(), baz.descriptors())
        self.assertEqual(
            set(Baz.descriptors()),
            set(['_id', 'string', 'number', 'bar_id', 'bar', 'hybrid_number']))

    def test_relationships(self):
        baz = Baz.get(1)

        # it should be a class and instance property
        self.assertEqual(Baz.relationships(), baz.relationships())
        self.assertEqual(set(Baz.relationships()), set(['bar']))

    def test_primary_attrs(self):
        baz = Baz.get(1)

        # it should be a class and instance property
        self.assertEqual(Baz.primary_attrs(), baz.primary_attrs())
        self.assertTrue([attr.property.is_primary()
                         for attr in Baz.primary_attrs()])

    def test_get(self):
        self.assertEqual(Foo.get(1), self.db.query(Foo).get(1))

    def test_get_by(self):
        self.assertEqual(
            Foo.get_by(string='Joe Smith'),
            self.db.query(Foo).filter_by(string='Joe Smith').first())
        self.assertEqual(
            Foo.get_by(dict(string='Joe Smith')),
            self.db.query(Foo).filter_by(string='Joe Smith').first())

    def test_filter(self):
        self.assertEqual(str(Foo.filter()), str(self.db.query(Foo).filter()))

    def test_filter_by(self):
        self.assertEqual(str(Foo.filter_by()),
                         str(self.db.query(Foo).filter_by()))

    def test_object_session(self):
        record = Foo.get(1)
        self.assertIs(record.object_session,
                      self.db.session.object_session(record))

    def test_query_session(self):
        self.assertIs(Foo.session(), Foo.query.session)

    def test_flush(self):
        record = Baz()
        self.db.add(record)

        self.assertIsNone(record._id)

        record.flush()

        self.assertIsNotNone(record._id)

    def test_delete(self):
        record = Baz()
        self.db.add_commit(record)

        _id = record._id

        self.assertIsNotNone(Baz.get(_id))

        record.delete()
        self.db.commit()

        self.assertIsNone(Baz.get(_id))

    def test_save(self):
        record = Foo.get(1)
        new_number = record.number * record.number + 1
        record.number = new_number

        record.save()
        self.db.commit()

        result = self.db.execute('select number from foo where _id=1')
        self.assertEqual(result.fetchone()[0], new_number)

    def test_expire(self):
        record = Foo.get(1)

        number = record.number
        new_number = number * number + 1

        # execute non-ORM transaction
        self.db.execute(
            'update foo set number = :n where _id = 1',
            params={'n': new_number})

        # it's value hasn't changed
        self.assertEqual(record.number, number)

        record.expire()

        # it's values are empty
        self.assertEqual(record.descriptor_dict, {})

        # it's values are reloaded on access
        self.assertEqual(record.number, new_number)
        self.assertNotEquals(record.descriptor_dict, {})

    def test_refresh(self):
        record = Foo.get(1)

        number = record.number
        new_number = number * number + 1

        # execute non-ORM transaction
        self.db.execute(
            'update foo set number = :n where _id = 1',
            params={'n': new_number})

        # it's value hasn't changed
        self.assertEqual(record.number, number)

        record.refresh()

        # it's values are empty
        # it's values are reloaded immediately
        self.assertNotEquals(record.to_dict(), {})
        self.assertEqual(record.number, new_number)

    def test_expunge(self):
        _id = 10
        record = Foo(_id=_id)

        # add record to session, expunge it, and then commit
        self.db.add(record)
        record.expunge()
        self.db.commit()

        # it should not have been added to the database
        self.assertIsNone(Foo.get(_id))

    def test_autogenerated_tablename(self):
        self.assertEqual(AutoGenTableName.__tablename__, 'auto_gen_table_name')

    def test_autogenerated_tablename_inherited_primary_key(self):
        self.assertEqual(InheritedAutoGenTableName.__tablename__,
                         'inherited_auto_gen_table_name')

    def test_single_primary_key(self):
        self.assertEqual(Foo.primary_key(), inspect(Foo).primary_key[0])

    def test_multiple_primary_keys(self):
        self.assertEqual(MultiplePrimaryKey.primary_key(),
                         inspect(MultiplePrimaryKey).primary_key)

    def test_inherited_table_args(self):
        class Abstract(object):
            id = Column(types.Integer(), primary_key=True)
            string = Column(types.String())
            number = Column(types.Integer())

            __local_table_args__ = (Index('idx_abstract_string', 'string'),
                                    Index('idx_abstract_number', 'number'),
                                    {'mysql_foo': 'bar', 'mysql_bar': 'bar'})

        class Mixin(object):
            name = Column(types.String())

            __local_table_args__ = (Index('idx_name', 'name'),)

        class Obj(Model, Mixin, Abstract):
            text = Column(types.Text())
            __local_table_args__ = (Index('idx_obj_text', 'text'),
                                    {'mysql_foo': 'foo'})

        self.assertEqual(Obj.__table_args__[-1],
                         {'mysql_foo': 'foo', 'mysql_bar': 'bar'})

        expected_indexes = ['idx_abstract_string',
                            'idx_abstract_number',
                            'idx_name',
                            'idx_obj_text']

        for i, name in enumerate(expected_indexes):
            self.assertEqual(Obj.__table_args__[i].name, name)
            self.assertIsInstance(Obj.__table_args__[i], Index)

    def test_inherited_table_args_callable(self):
        class AbstractCM(object):
            id = Column(types.Integer(), primary_key=True)
            string = Column(types.String())
            number = Column(types.Integer())

            __local_table_args__ = (Index('idx_cm_abstract_string', 'string'),
                                    Index('idx_cm_abstract_number', 'number'),
                                    {'mysql_foo': 'bar', 'mysql_bar': 'bar'})

        class MixinCM(object):
            name = Column(types.String())

            def __local_table_args__():
                return (Index('idx_cm_name', 'name'),)

        class ObjCM(Model, MixinCM, AbstractCM):
            text = Column(types.Text())

            @classmethod
            def __local_table_args__(cls):
                return (Index('idx_cm_obj_text', 'text'),
                        {'mysql_foo': 'foo'})

        self.assertEqual(ObjCM.__table_args__[-1],
                         {'mysql_foo': 'foo', 'mysql_bar': 'bar'})

        expected_indexes = ['idx_cm_abstract_string',
                            'idx_cm_abstract_number',
                            'idx_cm_name',
                            'idx_cm_obj_text']

        for i, name in enumerate(expected_indexes):
            self.assertEqual(ObjCM.__table_args__[i].name, name)
            self.assertIsInstance(ObjCM.__table_args__[i], Index)

    def test_inherited_mapper_args(self):
        class Abstract(object):
            id = Column(types.Integer(), primary_key=True)
            string = Column(types.String())
            number = Column(types.Integer())

            __local_mapper_args__ = {'column_prefix': '_',
                                     'order_by': 'number'}

        class Mixin(object):
            name = Column(types.String())

            __local_mapper_args__ = {'column_prefix': '__'}

        class Obj2(Model, Mixin, Abstract):
            text = Column(types.Text())
            __local_mapper_args__ = {'order_by': 'string'}

        self.assertEqual(Obj2.__mapper_args__,
                         {'column_prefix': '__', 'order_by': 'string'})

    def test_is_modified(self):
        record = Foo.get(1)
        self.assertEqual(record.is_modified(), False)

        record.number += 1
        self.assertEqual(record.is_modified(), True)

        record.refresh()
        self.assertEqual(record.is_modified(), False)
