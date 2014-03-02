# Types

Collection of custom column types.

## DeclarativeEnum

An enum type which can be used in declarative model definitions.

```python
class OrderStatus(DeclarativeEnum):
    pending = ('p', 'Pending')
    submitted = ('s', 'Submitted')
    complete = ('c', 'Complete')

class Order(Model):
    status = Column(OrderStatus.db_type(), default=OrderStatus.pending)
```
### Class Methods

#### db_type()

Return the column type for use in `Column` definition.

```python
class Order(Model):
    status = Column(OrderStatus.db_type(), default=OrderStatus.pending)
```

#### from_string()

Return enum symbol given string value.

```python
order.status = OrderStatus.from_string('p')
```

#### values()

Return list of possible enum values. Each value is a valid argument to `from_string()`.

```python
values = OrderStatus.values()
assert values == ['p', 's', 'c']
```
