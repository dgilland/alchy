# Model Events

SQLAlchemy features an ORM event API but one thing that is lacking is a way to register event handlers in a declarative way inside the Model's class definition. To bridge this gap, `alchy.events` contains a collection of decorators that enable this kind of functionality.

Instead of having to write event registration like this:

```python
from sqlalchemy import event

from project.core import Model

class User(Model):
    _id = Column(types.Integer(), primary_key=True)
    email = Column(types.String())

def set_email_listener(target, value, oldvalue, initiator):
    print 'received "set" event for target: {0}'.format(target)
    return value

def before_insert_listener(mapper, connection, target):
    print 'received "before_insert" event for target: {0}'.format(target)

event.listen(User.email, 'set', set_email_listener, retval=True)
event.listen(User, 'before_insert, before_insert_listener)
```

Model Events allows one to write event registration more succinctly as:

```python
from alchy import events

from project.core import Model

class User(Model):
    _id = Column(types.Integer(), primary_key=True)
    email = Column(types.String())

    @events.on_set('email', retval=True)
    def on_set_email(target, value, oldvalue, initiator):
        print 'received set event for target: {0}'.format(target)
        return value

    @events.before_insert
    def before_insert(mapper, connection, target):
        print 'received "before_insert" event for target: {0}'.format(target)
```

Keep in mind that when defining event handlers on a Model class, the function signature should look like a `staticmethod` function but without the `@staticmethod` decorator.

For details on each event type's expected function signature, see SQLAlchemy's [ORM Events](http://docs.sqlalchemy.org/en/latest/orm/events.html).

## Attribute Events

### @on_set

```python
class MyModel(Model):
    ...
    @events.on_set('attribute_name', **event_kargs)
    def on_set(target, value, oldvalue, initiator):
        pass
```

### @on_append

```python
class MyModel(Model):
    ...
    @events.on_append('attribute_name', **event_kargs)
    def on_append(target, value, initiator):
        pass
```

### @on_remove

```python
class MyModel(Model):
    ...
    @events.on_remove('attribute_name', **event_kargs)
    def on_append(target, value, initiator):
        pass
```

## Mapper Events

### @before_delete

```python
class MyModel(Model):
    ...
    @events.before_delete
    def before_delete(target, value, initiator):
        pass

    # or...

    @events.before_delete(**event_kargs)
    def before_delete(target, value, initiator):
        pass
```

### @before_insert

```python
class MyModel(Model):
    ...
    @events.before_insert
    def before_insert(target, value, initiator):
        pass

    # or...

    @events.before_insert(**event_kargs)
    def before_insert(target, value, initiator):
        pass
```

### @before_update

```python
class MyModel(Model):
    ...
    @events.before_update
    def before_update(target, value, initiator):
        pass

    # or...

    @events.before_update(**event_kargs)
    def before_update(target, value, initiator):
        pass
```

### @before_insert_update

This is a composite event which listens for both `before_insert` and `before_update` events.

```python
class MyModel(Model):
    ...
    @events.before_insert_update
    def before_insert_update(target, value, initiator):
        pass

    # or...

    @events.before_insert_update(**event_kargs)
    def before_insert_update(target, value, initiator):
        pass
```

### @after_delete

```python
class MyModel(Model):
    ...
    @events.after_delete
    def after_delete(target, value, initiator):
        pass

    # or...

    @events.after_delete(**event_kargs)
    def after_delete(target, value, initiator):
        pass
```

### @after_insert

```python
class MyModel(Model):
    ...
    @events.after_insert
    def after_insert(target, value, initiator):
        pass

    # or...

    @events.after_insert(**event_kargs)
    def after_insert(target, value, initiator):
        pass
```

### @after_update

```python
class MyModel(Model):
    ...
    @events.after_update
    def after_update(target, value, initiator):
        pass

    # or...

    @events.after_update(**event_kargs)
    def after_update(target, value, initiator):
        pass
```

### @after_insert_update

This is a composite event which listens for both `after_insert` and `after_update` events.

```python
class MyModel(Model):
    ...
    @events.after_insert_update
    def after_insert_update(target, value, initiator):
        pass

    # or...

    @events.after_insert_update(**event_kargs)
    def after_insert_update(target, value, initiator):
        pass
```

### @on_append_result

```python
class MyModel(Model):
    ...
    @events.on_append_result
    def on_append_result(mapper, context, row, target, result, **flags):
        pass

    # or...

    @events.on_append_result(**event_kargs)
    def on_append_result(mapper, context, row, target, result, **flags):
        pass
```

### @on_create_instance

```python
class MyModel(Model):
    ...
    @events.on_create_instance
    def on_create_instance(mapper, context, row, class_):
        pass

    # or...

    @events.on_create_instance(**event_kargs)
    def on_create_instance(mapper, context, row, class_):
        pass
```

### @on_instrument_class

```python
class MyModel(Model):
    ...
    @events.on_instrument_class
    def on_instrument_class(mapper, class_):
        pass

    # or...

    @events.on_instrument_class(**event_kargs)
    def on_instrument_class(mapper, class_):
        pass
```

### @before_configured

```python
class MyModel(Model):
    ...
    @events.before_configured
    def before_configured():
        pass
```

### @after_configured

```python
class MyModel(Model):
    ...
    @events.after_configured
    def after_configured():
        pass
```

### @on_mapper_configured

```python
class MyModel(Model):
    ...
    @events.on_mapper_configured
    def on_mapper_configured(mapper, class_):
        pass

    # or...

    @events.on_mapper_configured(**event_kargs)
    def on_mapper_configured(mapper, class_):
        pass
```

### @on_populate_instance

```python
class MyModel(Model):
    ...
    @events.on_populate_instance
    def on_populate_instance(mapper, context, row, target, **flags):
        pass

    # or...

    @events.on_populate_instance(**event_kargs)
    def on_populate_instance(mapper, context, row, target, **flags):
        pass
```

### @on_translate_row

```python
class MyModel(Model):
    ...
    @events.on_translate_row
    def on_translate_row(mapper, context, row):
        pass

    # or...

    @events.on_translate_row(**event_kargs)
    def on_translate_row(mapper, context, row):
        pass
```

## Instance Events

### @on_expire

```python
class MyModel(Model):
    ...
    @events.on_expire
    def on_expire(target, attrs):
        pass

    # or...

    @events.on_expire(**event_kargs)
    def on_expire(target, attrs):
        pass
```

### @on_load

```python
class MyModel(Model):
    ...
    @events.on_load
    def on_load(target, context):
        pass

    # or...

    @events.on_load(**event_kargs)
    def on_load(target, context):
        pass
```

### @on_refresh

```python
class MyModel(Model):
    ...
    @events.on_refresh
    def on_refresh(target, context, attrs):
        pass

    # or...

    @events.on_refresh(**event_kargs)
    def on_refresh(target, context, attrs):
        pass
```
