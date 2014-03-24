
from unittest import TestCase

from alchy import manager
from alchy._compat import iteritems

from . import fixtures


class TestBase(TestCase):

    config = {
        'SQLALCHEMY_DATABASE_URI': 'sqlite://'
    }

    @property
    def models(self):
        return fixtures.Models.values()

    @property
    def models_dict(self):
        return fixtures.Models

    @property
    def model_table_names(self):
        return [m.__tablename__ for m in self.models]

    def has_table(self, engine, table_name):
        return engine.dialect.has_table(engine.connect(), table_name)

    def assertTableExists(self, engine, table_name):
        self.assertTrue(self.has_table(engine, table_name))

    def assertTableNotExists(self, engine, table_name):
        self.assertFalse(self.has_table(engine, table_name))

    def assertModelTablesExist(self, engine):
        for table_name in self.model_table_names:
            self.assertTableExists(engine, table_name)

    def assertModelTablesNotExists(self, engine):
        for table_name in self.model_table_names:
            self.assertTableNotExists(engine, table_name)

    ##
    # polyfills for python2.6 supports
    ##
    def assertIsNone(self, a, msg=None):
        try:
            assert a is None
        except AssertionError:
            if msg:
                raise AssertionError(msg)
            else:
                raise

    def assertIsNotNone(self, a, msg=None):
        try:
            assert a is not None
        except AssertionError:
            if msg:
                raise AssertionError(msg)
            else:
                raise

    def assertIs(self, a, b, msg=None):
        try:
            assert a is b
        except AssertionError:
            if msg:
                raise AssertionError(msg)
            else:
                raise

    def assertIsInstance(self, a, b, msg=None):
        try:
            assert isinstance(a, b)
        except AssertionError:
            if msg:
                raise AssertionError(msg)
            else:
                raise

    def assertIn(self, a, b, msg=None):
        try:
            assert a in b
        except AssertionError:
            if msg:
                raise AssertionError(msg)
            else:
                raise

    def assertNotIn(self, a, b, msg=None):
        try:
            assert a not in b
        except AssertionError:
            if msg:
                raise AssertionError(msg)
            else:
                raise


class TestQueryBase(TestBase):

    @classmethod
    def setUpClass(cls):
        cls.db = manager.Manager(Model=fixtures.Model, config=cls.config)

    @classmethod
    def tearDownClass(cls):
        cls.db.session.close()

    def setUp(self):
        self.db.create_all()

        for model_name, Model in iteritems(self.models_dict):
            records = fixtures.data.get(model_name, [])
            for r in records:
                self.db.session.add(Model(**r))

        self.db.session.commit()

    def tearDown(self):
        self.db.close()
        self.db.drop_all()
