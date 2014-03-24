# Manager

The `Manager` class helps manage a SQLAlchemy database session as well as provide convenience functions for commons operations.

## Configuration

The following configuration values are support can be passed into a new `Manager` instance as a `dict`, `class`, or `module`.

|||
|-|-|
| `SQLALCHEMY_DATABASE_URI` | URI used to connect to the database. Defaults to `sqlite://`. |
| `SQLALCHEMY_BINDS` | A `dict` that maps bind keys to database URIs. Optionally, in place of a database URI, a configuration `dict` can be used to overrided connection options. |
| `SQLALCHEMY_ECHO` | When `True` have SQLAlchemy echo all SQL statements. Defaults to `False`. |
| `SQLALCHEMY_POOL_SIZE` | The size of the database pool. Defaults to the engine’s default (usually `5`). |
| `SQLALCHEMY_POOL_TIMEOUT` | Specifies the connection timeout for the pool. Defaults to `10`. |
| `SQLALCHEMY_POOL_RECYCLE` | Number of seconds after which a connection is automatically recycled. |
| `SQLALCHEMY_MAX_OVERFLOW` | Controls the number of connections that can be created after the pool reached its maximum size. When those additional connections are returned to the pool, they are disconnected and discarded. |

## Methods

### \_\_init\_\_()

Initialization of `Manager` accepts a config object, session options, and an optional declarative base. If `Model` isn't provided, then a default one is generated using `make_declarative_base()`. The declarative base model is accessible at `manager.Model`.


```python
Manager(config=None, session_options=None, Model=None)

config = {
    'SQLALCHEMY_DATABASE_URI': 'sqlite://test.db'
}

db = Manager(config=config)
db.Model
```

By default, the `session_options` are:

```python
query_cls = alchy.Query
autocommit = False
autoflush = True
```

### create_all()

Call `Model.metadata.create_all()`. Optionally, limit operation to a particular database bind.

```python
db.create_all(bind='__all__')

db.create_all(bind='users')
```

### drop_all()

Call `Model.metadata.drop_all()`. Optionally, limit operation to a particular database bind.

```python
db.drop_all(bind='__all__')

db.drop_all(bind='users')
```

### reflect()

Call `Model.metadata.()`. Optionally, limit operation to a particular database bind.

```python
db.reflect(bind='__all__')

db.reflect(bind='users')
```

### add()

Call a modified verson of `session.add()`. Accepts a single object, list of objects, or position arguments of objects to add. Functions similarly to `session.add_all()` but with a more permissive call signature.

```python
db.add(*instances)

db.add(user1)
db.add(user1, user2)
db.add([user1, user2)
db.add(user1).add(user2)
```

### add_commit()

Calls `add()` followed by `session.commit()`.

```python
db.add_commit(*instances)

db.add_commit(user1, user2)
```

### delete()

Call a modified verson of `session.delete()`. Accepts a single object, list of objects, or position arguments of objects to add. Functions similarly to `session.add_all()` but with a more permissive call signature.

```python
db.delete(*instances)

db.delete(user1)
db.delete(user1, user2)
db.delete([user1, user2])
db.delete(user1).delete(user2)
```

### delete_commit()

Calls `delete()` followed by `session.commit()`.

```python
db.delete_commit(*instances)

db.delete_commit(user1, user2)
```

### \_\_getattr\_\_

Proxy attribute access to `session` object.

```python
db.query is db.session.query
db.commit is db.session.commit
db.rollback is db.session.rollback
db.close is db.session.close
# etc...
```

## Properties

### metadata

Proxy to `Model.metadata`.

```python
db.metadata is db.Model.metadata
```

### engine

Proxy to `session.get_bind()`.

```python
db.engine is db.session.get_bind()
```
