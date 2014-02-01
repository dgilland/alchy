
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

        self.assertEquals(test_order.status.name, 'pending')
        self.assertEquals(test_order.status.value, 'p')
        self.assertEquals(test_order.status.description, 'Pending')

        self.assertEquals(str(test_order.status), 'pending')
        self.assertEquals(repr(test_order.status), '<pending>')

