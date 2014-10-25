
import pickle

import sqlalchemy

from .base import TestQueryBase
from .fixtures import OrderStatus, OrderSide, Order


class TestDeclarativeEnum(TestQueryBase):

    def test_type(self):
        self.assertIsInstance(
            OrderStatus.db_type().impl, sqlalchemy.types.Enum)

    def test_attributes(self):
        test_order = self.db.query(Order).first()

        self.assertTrue(hasattr(test_order.status, 'name'))
        self.assertTrue(hasattr(test_order.status, 'value'))
        self.assertTrue(hasattr(test_order.status, 'description'))

        self.assertTrue(hasattr(test_order.side, 'name'))
        self.assertTrue(hasattr(test_order.side, 'value'))
        self.assertTrue(hasattr(test_order.side, 'description'))

        test_order.status = OrderStatus.pending
        test_order.side = OrderSide.sell
        self.db.add_commit(test_order)

        self.assertEqual(test_order.status.name, 'pending')
        self.assertEqual(test_order.status.value, 'p')
        self.assertEqual(test_order.status.description, 'Pending')

        self.assertEqual(str(test_order.status), 'pending')
        self.assertEqual(repr(test_order.status), '<pending>')

        self.assertEqual(test_order.side.name, 'sell')
        self.assertEqual(test_order.side.value, 's')
        self.assertEqual(test_order.side.description, 'Sell')

        self.assertEqual(str(test_order.side), 'sell')
        self.assertEqual(repr(test_order.side), '<sell>')

    def test_pickle(self):
        status = OrderStatus.complete
        pickled = pickle.dumps(status)
        unpickled = pickle.loads(pickled)
        self.assertIs(unpickled, status)

        side = OrderSide.buy
        pickled = pickle.dumps(side)
        unpickled = pickle.loads(pickled)
        self.assertIs(unpickled, side)

    def test_from_string(self):
        self.assertIs(OrderStatus.from_string('p'), OrderStatus.pending)
        self.assertRaises(ValueError, OrderStatus.from_string, 'invalid')

        self.assertIs(OrderSide.from_string('b'), OrderSide.buy)
        self.assertRaises(ValueError, OrderSide.from_string, 'invalid')

    def test_iter_support(self):
        self.assertTrue(len(list(OrderStatus)) > 0)

        for status in OrderStatus:
            self.assertTrue(hasattr(OrderStatus, status.name))
            self.assertIs(OrderStatus.from_string(status.value),
                          getattr(OrderStatus, status.name))

        self.assertTrue(len(list(OrderSide)) > 0)

        for side in OrderSide:
            self.assertTrue(hasattr(OrderSide, side.name))
            self.assertIs(OrderSide.from_string(side.value),
                          getattr(OrderSide, side.name))

    def test_to_dict(self):
        self.assertEqual(OrderStatus.pending.to_dict(),
                         {'value': 'p', 'description': 'Pending'})

        self.assertEqual(OrderSide.sell.to_dict(),
                         {'value': 's', 'description': 'Sell'})
