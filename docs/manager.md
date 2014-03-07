# Manager

The `Manager` class helps manage a SQLAlchemy database session as well as provide convenience functions for commons operations.

## Methods

### \_\_init\_\_()

Initialization of `Manager` requires a `config` dict and an optional declarative base, `Model`. If `Model` isn't provided, then a default one is generated using `make_declarative_base()` and then accessible at `manager.Model`.

```python
db = Manager(config, Model=None, engine_config_prefix='')

config = {
	'engine': {'url': 'sqlite://'},
	'session': {'autocommit': True}
}

db = Manager(config=config)
db.Model
```

### create_all()

Call `Model.metadata.create_all()`.

```python
db.create_all()
```

### drop_all()

Call `Model.metadata.drop_all()`.

```python
db.drop_all()
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
