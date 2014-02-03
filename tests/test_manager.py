
from sqlalchemy import create_engine
from sqlalchemy.exc import UnboundExecutionError

from alchy import manager, model

from .base import TestBase
import fixtures

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

