
import os
import glob

from sqlalchemy import Column, types
from sqlalchemy.exc import UnboundExecutionError
from sqlalchemy.orm.exc import UnmappedError

from alchy import manager, model, Session

from .base import TestBase, TestQueryBase
from . import fixtures
from .fixtures import Foo


class TestManager(TestBase):

    def test_create_drop_all(self):
        db = manager.Manager(Model=fixtures.Model, config=self.config)

        db.create_all()

        self.assertTrue(len(self.models) > 0)
        self.assertModelTablesExist(db.engine)

        db.drop_all()

        self.assertModelTablesNotExists(db.engine)

    def test_default_model_config(self):
        db = manager.Manager(config=self.config)

        self.assertTrue(issubclass(db.Model, model.ModelBase))

    def test_create_all_exception(self):
        # pass in dummy value for Model
        db = manager.Manager(Model=False, config=self.config)
        self.assertRaises(UnmappedError, db.create_all)

    def test_drop_all_exception(self):
        # pass in dummy value for Model
        db = manager.Manager(Model=False, config=self.config)
        self.assertRaises(UnmappedError, db.drop_all)


class TestManagerSessionExtensions(TestQueryBase):

    def get_count(self, table='foo'):
        return self.db.execute(
            'select count(*) from {0}'.format(table)).scalar()

    def test_add(self):
        count = self.get_count()
        self.db.add(Foo())
        self.db.add(Foo(), Foo())
        self.db.add([Foo(), Foo()])

        self.assertEqual(self.db.execute(
            'select count(*) from foo').scalar(), count)

        self.db.commit()

        self.assertEqual(self.get_count(), count + 5)

    def test_add_commit(self):
        count = self.get_count()

        self.db.add_commit(Foo())
        self.assertEqual(self.get_count(), count + 1)

        self.db.add_commit(Foo(), Foo())
        self.assertEqual(self.get_count(), count + 3)

        self.db.add_commit([Foo(), Foo()])
        self.assertEqual(self.get_count(), count + 5)

    def test_delete(self):
        count = self.get_count()
        foos = Foo.query.all()

        self.db.delete(foos[0])
        self.db.delete(foos[1], foos[2])
        self.db.delete([foos[3], foos[4]])

        self.assertEqual(self.get_count(), count)

        self.db.commit()

        self.assertEqual(self.get_count(), count - 5)

    def test_delete_commit(self):
        count = self.get_count()
        foos = Foo.query.all()

        self.db.delete_commit(foos[0])
        self.assertEqual(self.get_count(), count - 1)

        self.db.delete_commit(foos[1], foos[2])
        self.assertEqual(self.get_count(), count - 3)

        self.db.delete_commit([foos[3], foos[4]])
        self.assertEqual(self.get_count(), count - 5)

    def test_custom_session(self):
        class MySession(Session):
            pass

        db = manager.Manager(session_class=MySession)
        self.assertIsInstance(db.session.session_factory(), MySession)


class TestMultipleEngineBinds(TestBase):
    class config(object):
        binds = [
            'sqlite:///bind0.test.db',
            'sqlite:///bind1.test.db',
            'sqlite:///bind2.test.db'
        ]

        SQLALCHEMY_DATABASE_URI = binds[0]
        SQLALCHEMY_BINDS = {
            'bind1': binds[1],
            'bind2': {
                'SQLALCHEMY_DATABASE_URI': binds[2]
            }
        }

    Model = model.make_declarative_base()

    class Bind0(Model):
        _id = Column(types.Integer(), primary_key=True)

    class Bind1(Model):
        __bind_key__ = 'bind1'

        _id = Column(types.Integer(), primary_key=True)

    class Bind2(Model):
        __bind_key__ = 'bind2'

        _id = Column(types.Integer(), primary_key=True)

    def setUp(self):
        self.db = manager.Manager(config=self.config, Model=self.Model)
        self.db.create_all()

        self.engine0 = self.db.engine
        self.engine1 = self.db.get_engine('bind1')
        self.engine2 = self.db.get_engine('bind2')

    def tearDown(self):
        for db in glob.glob('*.test.db'):
            os.remove(db)

    def test_bind_engines(self):
        """Test that each bind engine is accessible and configured properly."""
        self.assertEqual(
            str(self.db.engine.url), self.config.binds[0])
        self.assertEqual(
            str(self.db.get_engine('bind1').url), self.config.binds[1])
        self.assertEqual(
            str(self.db.get_engine('bind2').url), self.config.binds[2])

    def test_bind_tables(self):
        """Test that tables are created in the proper database."""
        self.assertEqual(
            self.engine0.execute('select * from bind0').fetchall(), [])
        self.assertEqual(
            self.engine1.execute('select * from bind1').fetchall(), [])
        self.assertEqual(
            self.engine2.execute('select * from bind2').fetchall(), [])

        try:
            self.engine0.execute('select * from bind1')
        except Exception as e:
            self.assertIn('no such table', str(e))

        try:
            self.engine0.execute('select * from bind2')
        except Exception as e:
            self.assertIn('no such table', str(e))

        try:
            self.engine1.execute('select * from bind0')
        except Exception as e:
            self.assertIn('no such table', str(e))

        try:
            self.engine1.execute('select * from bind2')
        except Exception as e:
            self.assertIn('no such table', str(e))

        try:
            self.engine2.execute('select * from bind0')
        except Exception as e:
            self.assertIn('no such table', str(e))

        try:
            self.engine2.execute('select * from bind1')
        except Exception as e:
            self.assertIn('no such table', str(e))

    def test_bind_inserts(self):
        """Test that records are inserted into the proper database when using
        models."""
        self.db.add_commit(self.Bind0())
        self.db.add_commit(self.Bind1())
        self.db.add_commit(self.Bind2())

        self.assertTrue(self.Bind0.query.count() > 0)
        self.assertEqual(
            self.Bind0.query.count(),
            self.engine0.execute('select count(*) from bind0').fetchone()[0])

        self.assertTrue(self.Bind1.query.count() > 0)
        self.assertEqual(
            self.Bind1.query.count(),
            self.engine1.execute('select count(*) from bind1').fetchone()[0])

        self.assertTrue(self.Bind2.query.count() > 0)
        self.assertEqual(
            self.Bind2.query.count(),
            self.engine2.execute('select count(*) from bind2').fetchone()[0])

    def test_create_drop_all_by_bind(self):
        """Test that create/drop all can be used to target a specific bind."""
        self.db.drop_all(bind='bind1')

        self.assertEqual(
            self.engine0.execute('select * from bind0').fetchall(), [])
        self.assertEqual(
            self.engine2.execute('select * from bind2').fetchall(), [])

        try:
            self.engine1.execute('select * from bind1')
        except Exception as e:
            self.assertIn('no such table', str(e))

        self.db.create_all(bind='bind1')

        self.assertEqual(
            self.engine1.execute('select * from bind1').fetchall(), [])

        self.db.drop_all(bind=['bind1', 'bind2'])

        try:
            self.engine1.execute('select * from bind1')
        except Exception as e:
            self.assertIn('no such table', str(e))

        try:
            self.engine2.execute('select * from bind2')
        except Exception as e:
            self.assertIn('no such table', str(e))

        self.db.create_all(bind=['bind1', 'bind2'])

        self.assertEqual(
            self.engine1.execute('select * from bind1').fetchall(), [])
        self.assertEqual(
            self.engine2.execute('select * from bind2').fetchall(), [])

    def test_reflect(self):
        """Test that existing database tables can be reflected."""
        rdb = manager.Manager(
            config={'SQLALCHEMY_DATABASE_URI': self.config.binds[0]})

        self.assertEqual(len(rdb.metadata.tables), 0)

        rdb.reflect()

        self.assertEqual(len(rdb.metadata.tables), 1)
        self.assertIn('bind0', rdb.metadata.tables)
