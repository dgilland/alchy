
import pickle

import sqlalchemy

from .base import TestQueryBase
from fixtures import OrderStatus, Order

class TestDeclarativeEnum(TestQueryBase):

    def test_type(self):
        self.assertIsInstance(OrderStatus.db_type().impl, sqlalchemy.types.Enum)

    def test_attributes(self):
        test_order = self.db.query(Order).first()

        self.assertTrue(hasattr(test_order.status, 'name'))
        self.assertTrue(hasattr(test_order.status, 'value'))
        self.assertTrue(hasattr(test_order.status, 'description'))

        test_order.status = OrderStatus.pending
        self.db.add_commit(test_order)

        self.assertEqual(test_order.status.name, 'pending')
        self.assertEqual(test_order.status.value, 'p')
        self.assertEqual(test_order.status.description, 'Pending')

        self.assertEqual(str(test_order.status), 'pending')
        self.assertEqual(repr(test_order.status), '<pending>')

    def test_pickle(self):
        status = OrderStatus.complete

        pickled = pickle.dumps(status)
        unpickled = pickle.loads(pickled)

        self.assertIs(unpickled, status)

    def test_from_string(self):
        self.assertIs(OrderStatus.from_string('p'), OrderStatus.pending)
        self.assertRaises(ValueError, OrderStatus.from_string, 'invalid')

    def test_iter_support(self):
        self.assertTrue(len(list(OrderStatus)) > 0)

        for status in OrderStatus:
            self.assertTrue(hasattr(OrderStatus, status.name))
            self.assertIs(OrderStatus.from_string(status.value), getattr(OrderStatus, status.name))

    def test_to_dict(self):
        self.assertEqual(OrderStatus.pending.to_dict(), {'value': 'p', 'description': 'Pending'})
