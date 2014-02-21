
from functools import wraps, partial
from collections import namedtuple

import sqlalchemy

Event = namedtuple('Event', ['name', 'listener', 'kargs'])

def event(event_name, f=None, **kargs):
    if callable(f):
        # being called as a decorator with no arguments
        return event(event_name)(f)
    else:
        # being called as decorator with arguments
        def decorator(f, *args, **kargs):
            f.__event__ = Event(event_name, f, kargs)

            @wraps(f)
            def wrapper(cls, *args, **kargs):
                return f(*args, **kargs)

            return wrapper

        return decorator

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

                events.append(Event(event_name, listener, kargs))

    # append events which were added via @event decorator
    events += [value.__event__ for value in dct.values() if hasattr(value, '__event__')]

    if events:
        # reassemble events dict into consistent form using Event objects as values
        events_dict = {}
        for event in events:
            sqlalchemy.event.listen(cls, event.name, event.listener, **event.kargs)
            events_dict.setdefault(event.name, []).append(event)

        dct['__events__'].update(events_dict)

##
# Mapper Events
# http://docs.sqlalchemy.org/en/latest/orm/events.html#mapper-events
##

before_delete = partial(event, 'before_delete')
before_insert = partial(event, 'before_insert')
before_update = partial(event, 'before_update')

after_delete = partial(event, 'after_delete')
after_insert = partial(event, 'after_insert')
after_update = partial(event, 'after_update')

append_result = partial(event, 'append_result')
create_instance = partial(event, 'create_instance')
instrument_class = partial(event, 'instrument_class')
before_configured = partial(event, 'before_configured')
after_configured = partial(event, 'after_configured')
mapper_configured = partial(event, 'mapper_configured')
populate_instance = partial(event, 'populate_instance')
translate_row = partial(event, 'translate_row')

##
# Attribute Events
# http://docs.sqlalchemy.org/en/latest/orm/events.html#attribute-events
##

##
# Instance Events
# http://docs.sqlalchemy.org/en/latest/orm/events.html#instance-events
##

