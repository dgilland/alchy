
from sqlalchemy import create_engine
from sqlalchemy.exc import UnboundExecutionError
from sqlalchemy.orm.exc import UnmappedError

from alchy import manager, model

from .base import TestBase, TestQueryBase
import fixtures
from fixtures import Foo

class TestManager(TestBase):

    def test_create_drop_all(self):
        db = manager.Manager(Model=fixtures.Model, config=self.config)

        db.create_all()

        self.assertTrue(len(self.models) > 0)
        self.assertModelTablesExist(db.engine)

        db.drop_all()

        self.assertModelTablesNotExists(db.engine)

    def test_lazy_engine_config(self):
        db = manager.Manager(Model=fixtures.Model)

        self.assertRaises(UnboundExecutionError, db.create_all)

        db.init_engine(self.config['engine'])

        db.create_all()

        self.assertModelTablesExist(db.engine)

        db.drop_all()

    def test_lazy_session_config(self):
        db = manager.Manager(Model=fixtures.Model)

        self.assertRaises(UnboundExecutionError, db.create_all)

        engine = create_engine(self.config['engine']['url'])

        db.init_session({'bind': engine})

        self.assertIs(db.engine, engine)

        db.create_all()

        self.assertModelTablesExist(db.engine)

        db.drop_all()

    def test_default_model_config(self):
        db = manager.Manager()

        self.assertTrue(issubclass(db.Model, model.ModelBase))

    def test_create_all_exception(self):
        # pass in dummy value for Model
        db = manager.Manager(Model=False)
        self.assertRaises(UnmappedError, db.create_all)

    def test_drop_all_exception(self):
        # pass in dummy value for Model
        db = manager.Manager(Model=False)
        self.assertRaises(UnmappedError, db.drop_all)

class TestManagerSessionExtensions(TestQueryBase):

    def get_count(self, table='foo'):
        return self.db.execute('select count(*) from {0}'.format(table)).scalar()

    def test_add(self):
        count = self.get_count()
        self.db.add(Foo())
        self.db.add(Foo(), Foo())
        self.db.add([Foo(), Foo()])

        self.assertEqual(self.db.execute('select count(*) from foo').scalar(), count)

        self.db.commit()

        self.assertEqual(self.get_count(), count+5)

    def test_add_commit(self):
        count = self.get_count()

        self.db.add_commit(Foo())
        self.assertEqual(self.get_count(), count+1)

        self.db.add_commit(Foo(), Foo())
        self.assertEqual(self.get_count(), count+3)

        self.db.add_commit([Foo(), Foo()])
        self.assertEqual(self.get_count(), count+5)

    def test_delete(self):
        count = self.get_count()
        foos = Foo.query.all()

        self.db.delete(foos[0])
        self.db.delete(foos[1], foos[2])
        self.db.delete([foos[3], foos[4]])

        self.assertEqual(self.get_count(), count)

        self.db.commit()

        self.assertEqual(self.get_count(), count-5)

    def test_delete_commit(self):
        count = self.get_count()
        foos = Foo.query.all()

        self.db.delete_commit(foos[0])
        self.assertEqual(self.get_count(), count-1)

        self.db.delete_commit(foos[1], foos[2])
        self.assertEqual(self.get_count(), count-3)

        self.db.delete_commit([foos[3], foos[4]])
        self.assertEqual(self.get_count(), count-5)

