
from sqlalchemy import orm

from alchy import query

from .base import TestQueryBase

import fixtures
from fixtures import Foo, Bar, Baz, Qux

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
        self.assertEquals(record._id, data['_id'])
        self.assertEquals(record.string, data['string'])
        self.assertEquals(record.number, data['number'])
        self.assertEquals(record.boolean, data['boolean'])

        self.assertFalse(hasattr(record, 'ignored_field'))

    def assertIsSubset(self, subset, superset):
        self.assertTrue(all(item in superset.items() for item in subset.items()))

    def assertIsNotSubset(self, subset, superset):
        self.assertRaises(AssertionError, self.assertIsSubset, subset, superset)

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

    def test_query_property(self):
        self.assertIsInstance(Foo.query, query.Query)
        self.assertEquals(self.db.query(Foo).filter_by(number=3).all(), Foo.query.filter_by(number=3).all())

    def test_to_dict_with_lazy(self):
        data = fixtures.data['Foo'][0]
        record = self.db.query(Foo).get(data['_id'])

        as_json = record.to_dict()

        # it should use default loading which is lazy
        self.assertIsSubset(data, as_json)
        self.assertEquals(set(as_json.keys()), set(['_id', 'string', 'number', 'boolean']))

    def test_to_dict_with_joined(self):
        data = fixtures.data['Foo'][0]
        record = self.db.query(Foo).options(
            orm.joinedload('bars').joinedload('bazs'),
            orm.joinedload('quxs')
        ).get(data['_id'])

        as_json = record.to_dict()

        # it should load relationships
        self.assertIsSubset(data, as_json)
        self.assertEquals(set(as_json.keys()), set(['_id', 'string', 'number', 'boolean', 'quxs', 'bars']))

        # and relationship's relationships
        self.assertIn('bazs', as_json['bars'][0])

    def test_attrs(self):
        baz = Baz.get(1)

        # it should be a class and instance property
        self.assertEquals(Baz.attrs, baz.attrs)
        self.assertEquals(set(Baz.attrs), set(['_id', 'string', 'number', 'bar_id', 'bar']))

    def test_columns(self):
        baz = Baz.get(1)

        # it should be a class and instance property
        self.assertEquals(Baz.columns, baz.columns)
        self.assertEquals(set(Baz.columns), set(['_id', 'string', 'number', 'bar_id']))

    def test_column_attrs(self):
        baz = Baz.get(1)

        # it should be a class and instance property
        self.assertEquals(Baz.column_attrs, baz.column_attrs)
        self.assertEquals(set(Baz.column_attrs), set([Baz._id.property, Baz.string.property, Baz.number.property, Baz.bar_id.property]))

    def test_descriptors(self):
        baz = Baz.get(1)

        # it should be a class and instance property
        self.assertEquals(Baz.descriptors, baz.descriptors)
        self.assertEquals(set(Baz.descriptors), set(['_id', 'string', 'number', 'bar_id', 'bar', 'hybrid_number']))

    def test_relationships(self):
        baz = Baz.get(1)

        # it should be a class and instance property
        self.assertEquals(Baz.relationships, baz.relationships)
        self.assertEquals(set(Baz.relationships), set(['bar']))

    def test_get(self):
        self.assertEquals(Foo.get(1), self.db.query(Foo).get(1))

    def test_session(self):
        record = Foo.get(1)
        self.assertIs(record.session, self.db.session.object_session(record))

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

    def test_expire(self):
        record = Foo.get(1)

        number = record.number
        new_number = number * number + 1

        # execute non-ORM transaction
        self.db.execute('update foo set number = :n where _id = 1', params={'n': new_number})

        # it's value hasn't changed
        self.assertEquals(record.number, number)

        record.expire()

        # it's values are empty
        self.assertEquals(record.to_dict(), {})

        # it's values are reloaded on access
        self.assertEquals(record.number, new_number)
        self.assertNotEquals(record.to_dict(), {})

    def test_refresh(self):
        record = Foo.get(1)

        number = record.number
        new_number = number * number + 1

        # execute non-ORM transaction
        self.db.execute('update foo set number = :n where _id = 1', params={'n': new_number})

        # it's value hasn't changed
        self.assertEquals(record.number, number)

        record.refresh()

        # it's values are empty
        # it's values are reloaded immediately
        self.assertNotEquals(record.to_dict(), {})
        self.assertEquals(record.number, new_number)

    def test_expunge(self):
        _id = 10
        record = Foo(_id=_id)

        # add record to session, expunge it, and then commit
        self.db.add(record)
        record.expunge()
        self.db.commit()

        # it should not have been added to the database
        self.assertIsNone(Foo.get(_id))

