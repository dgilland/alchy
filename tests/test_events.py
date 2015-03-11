
import sqlalchemy
from sqlalchemy import orm, Column, types, ForeignKey

from alchy import model, query, manager, events

from .base import TestQueryBase


Model = model.make_declarative_base()


class TestEventsBase(TestQueryBase):
    @classmethod
    def setUpClass(cls):
        cls.db = manager.Manager(Model=Model, config=cls.config)

    def setUp(self):
        self.db.create_all()

    def tearDown(self):
        self.db.drop_all()


class TestEvents(TestEventsBase):
    """Test Model events"""

    class Huey(Model):
        event_tracker = {}

        __tablename__ = 'huey'
        __events__ = {
            'before_insert': 'before_insert',
            'after_insert': [
                'after_insert1',
                'after_insert2',
                ('after_insert3', {'raw': True})
            ],
            'on_set': [('on_set_name', {'attribute': 'name'})]
        }

        _id = Column(types.Integer(), primary_key=True)
        name = Column(types.String())
        dewey_id = Column(types.Integer(), ForeignKey('dewey._id'))

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

        def on_set_name(target, value, oldvalue, initator):
            target.event_tracker['set_name'] = 1

    class Dewey(Model):
        __tablename__ = 'dewey'
        __events__ = None

        _id = Column(types.Integer(), primary_key=True)
        name = Column(types.String())
        number = Column(types.Integer())
        min_hueys = Column(types.Boolean())
        hueys = orm.relationship('Huey')

        @events.before_insert()
        def before_insert(mapper, connection, target):
            target.name = 'Dewey'

        @events.on_set('name', retval=True)
        def on_set_name(target, value, oldvalue, initator):
            if oldvalue is None or (
                    hasattr(oldvalue, '__class__') and
                    oldvalue.__class__.__name__ == 'symbol'):
                # oldvalue is a symbol for either NO_VALUE or NOT_SET so allow
                # update
                return value
            else:
                # value previously set, so prevent edit
                return oldvalue

        @events.on_append('hueys')
        def on_append_hueys(target, value, intiator):
            if len(target.hueys) >= 1:
                target.min_hueys = True

        @events.on_remove('hueys')
        def on_remove_hueys(target, value, initator):
            if not len(target.hueys) >= 1:
                target.min_hueys = False

        @events.before_insert_update()
        def before_edit(mapper, connection, target):
            target.number = (target.number or 0) + 1

    def tearDown(self):
        super(TestEvents, self).tearDown()

        # clear event tracker
        self.Huey.event_tracker.clear()

    def test_events_using_class_attribute(self):
        h = self.Huey()
        self.db.add_commit(h)

        self.assertEqual(len(h.event_tracker['before_insert']), 0)
        self.assertEqual(len(h.event_tracker['after_insert1']), 1)
        self.assertEqual(h.name, 'Huey')
        self.assertEqual(h.event_tracker['after_insert2'], 2)
        self.assertEqual(h.event_tracker['set_name'], 1)

    def test_events_using_decorator(self):
        d = self.Dewey()

        self.assertIsNone(d.number)

        self.db.add_commit(d)

        self.assertEqual(d.number, 1)
        self.assertEqual(d.name, 'Dewey')

        # trigger update event
        d.name = 'Foo'
        self.db.commit()

        self.assertEqual(d.number, 2)

    def test_attribute_event_set(self):
        name = 'mister'

        d = self.Dewey()
        d.name = name
        d.name = 'no change'

        self.assertEqual(d.name, name)

        d = self.Dewey(name=name)
        d.name = 'no change'

        self.assertEqual(d.name, name)

    def test_attribute_event_append(self):
        d = self.Dewey()
        self.assertIsNone(d.min_hueys)
        d.hueys.append(self.Huey())
        self.assertIsNone(d.min_hueys)
        d.hueys.append(self.Huey())
        self.assertTrue(d.min_hueys)

    def test_attribute_event_remove(self):
        d = self.Dewey(hueys=[self.Huey(), self.Huey()])
        self.assertTrue(d.min_hueys)
        d.hueys.remove(d.hueys[0])
        self.assertTrue(d.min_hueys)
        d.hueys.remove(d.hueys[0])
        self.assertFalse(d.min_hueys)


class TestInstanceEvents(TestEventsBase):
    class Louie(Model):
        event_tracker = {}

        _id = Column(types.Integer(), primary_key=True)
        name = Column(types.String())

        @events.on_expire()
        def on_expire(target, attrs):
            target.event_tracker['expire'] = True

        @events.on_load()
        def on_load(target, context):
            target.event_tracker['load'] = True

        @events.on_refresh()
        def on_refresh(target, context, attrs):
            target.event_tracker['refresh'] = True

    def tearDown(self):
        super(TestInstanceEvents, self).tearDown()
        # clear event tracker
        self.Louie.event_tracker.clear()

    def test_expire(self):
        self.db.add(self.Louie())
        record = self.Louie.get(1)
        self.assertIsNone(record.event_tracker.get('expire'))
        record.expire()
        self.assertTrue(record.event_tracker.get('expire'))

    def test_load(self):
        self.db.add_commit(self.Louie())
        record = self.Louie.get(1)
        self.assertTrue(record.event_tracker.get('load'))

    def test_refresh(self):
        record = self.Louie()
        self.db.add_commit(record)
        self.assertIsNone(record.event_tracker.get('refresh'))
        self.assertIsNone(record.event_tracker.get('refresh'))
        self.Louie.get(1)
        self.assertTrue(record.event_tracker.get('refresh'))
