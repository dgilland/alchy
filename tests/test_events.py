
import sqlalchemy
from sqlalchemy import orm, Column, types

from alchy import model, query, manager, events

from .base import TestQueryBase

class TestModelEvents(TestQueryBase):
    '''Test Model events'''

    Model = model.make_declarative_base()

    class Huey(Model):
        event_tracker = {}

        __tablename__ = 'huey'
        __events__ = {
            'before_insert': 'before_insert',
            'after_insert': ['after_insert1', 'after_insert2', ('after_insert3', {'raw': True})],
            #'set': [('name', '
        }

        _id = Column(types.Integer(), primary_key=True)
        name = Column(types.String())

        def before_insert(mapper, connection, target):
            target.event_tracker['before_insert'] = target.query.all()
            target.name = 'Huey'

        def after_insert1(mapper, connection, target):
            target.event_tracker['after_insert1'] = target.query.all()
            target.event_tracker['after_insert2'] = 1

        def after_insert2(mapper, connection, target):
            target.event_tracker['after_insert2'] += 1

        def after_insert3(mapper, connection, target):
            from sqlalchemy.orm.state import InstanceState
            assert isinstance(target, InstanceState)

    class Dewey(Model):
        __tablename__ = 'dewey'
        __events__ = None

        _id = Column(types.Integer(), primary_key=True)
        name = Column(types.String())

        @events.before_insert
        def before_insert(mapper, connection, target):
            target.name = 'Dewey'

    @classmethod
    def setUpClass(cls):
        cls.db = manager.Manager(Model=cls.Model, config=cls.config)

    def setUp(self):
        self.db.create_all()

        # clear event tracker before each test
        self.Huey.event_tracker.clear()

    def test_events_using_class_attribute(self):
        h = self.Huey()
        self.db.add_commit(h)

        self.assertEqual(len(h.event_tracker['before_insert']), 0)
        self.assertEqual(len(h.event_tracker['after_insert1']), 1)
        self.assertEqual(h.name, 'Huey')
        self.assertEqual(h.event_tracker['after_insert2'], 2)

    def test_events_using_decorator(self):
        d = self.Dewey()
        self.db.add_commit(d)

        self.assertEqual(d.name, 'Dewey')

        d.name = 'Bob'

        # call event manually
        d.before_insert(None, None, d)

        self.assertEqual(d.name, 'Dewey')
