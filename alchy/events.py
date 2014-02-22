
from functools import wraps, partial
from collections import namedtuple

import sqlalchemy

Event = namedtuple('Event', ['name', 'attribute', 'listener', 'kargs'])

def make_event_decorator(event_name, attribute=None, **event_kargs):
    def decorator(f):
        # Attach event object to function which will be picked up in `register()`.
        f.__event__ = Event(event_name, attribute, f, event_kargs)

        # Notice that `decorated()` below takes a `self` argument but doesn't pass
        # it to `f()`. This is because we are enforcing a class method definition
        # similar to @staticemethod where the `self` or `cls` isn't included. But
        # since we don't want to require @staticmethod and since we don't want the
        # event listener to have access to self (due to event listener restrictions),
        # we're consuming `self` here and not passing it along. This is also
        # required since all events are registered in the metaclass, so the class
        # method definition needs to be compatible with `sqlalchemy.event.listen()`
        @wraps(f)
        def decorated(self, *args, **kargs):
            return f(*args, **kargs)
        return decorated

    return decorator

attribute_event = make_event_decorator

def mapper_event(event_name, f=None, **event_kargs):
    if callable(f):
        # being called as a decorator with no arguments
        return mapper_event(event_name)(f)
    else:
        # being called as decorator with arguments
        return make_event_decorator(event_name, attribute=None, **event_kargs)

def register(cls, dct):
    events = []

    # append class attribute defined events
    if dct.get('__events__'):
        # events defined on __events__ can have many forms (e.g. string based, list of tuples, etc)
        # so we need to iterate over them and parse into standardized Event object
        for event_name, listeners in dct['__events__'].iteritems():
            if not isinstance(listeners, list):
                listeners = [listeners]

            for listener in listeners:
                if isinstance(listener, tuple):
                    # listener definition includes event.listen keyword args
                    listener, kargs = listener
                else:
                    kargs = {}

                if not callable(listener):
                    # assume listener is a string reference to class method
                    listener = dct[listener]

                events.append(Event(event_name, kargs.pop('attribute', None), listener, kargs))

    # append events which were added via @event decorator
    events += [value.__event__ for value in dct.values() if hasattr(value, '__event__')]

    if events:
        # reassemble events dict into consistent form using Event objects as values
        events_dict = {}
        for event in events:
            obj = cls if event.attribute is None else getattr(cls, event.attribute)
            sqlalchemy.event.listen(obj, event.name, event.listener, **event.kargs)
            events_dict.setdefault(event.name, []).append(event)

        dct['__events__'].update(events_dict)


##
# Attribute Events
# http://docs.sqlalchemy.org/en/latest/orm/events.html#attribute-events
##

set_ = partial(attribute_event, 'set')
append = partial(attribute_event, 'append')
remove = partial(attribute_event, 'remove')

##
# Mapper Events
# http://docs.sqlalchemy.org/en/latest/orm/events.html#mapper-events
##

before_delete = partial(mapper_event, 'before_delete')
before_insert = partial(mapper_event, 'before_insert')
before_update = partial(mapper_event, 'before_update')

after_delete = partial(mapper_event, 'after_delete')
after_insert = partial(mapper_event, 'after_insert')
after_update = partial(mapper_event, 'after_update')

append_result = partial(mapper_event, 'append_result')
create_instance = partial(mapper_event, 'create_instance')
instrument_class = partial(mapper_event, 'instrument_class')
before_configured = partial(mapper_event, 'before_configured')
after_configured = partial(mapper_event, 'after_configured')
mapper_configured = partial(mapper_event, 'mapper_configured')
populate_instance = partial(mapper_event, 'populate_instance')
translate_row = partial(mapper_event, 'translate_row')

##
# Instance Events
# http://docs.sqlalchemy.org/en/latest/orm/events.html#instance-events
##

# @todo

