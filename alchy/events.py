
from functools import wraps, partial
from collections import namedtuple

import sqlalchemy

Event = namedtuple('Event', ['name', 'attribute', 'listener', 'kargs'])

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

    # add events which were added via @event decorator
    for value in dct.values():
        if hasattr(value, '__event__'):
            if not isinstance(value.__event__, list): # pragma: no cover
                value.__event__ = [value.__event__]
            events.extend(value.__event__)

    if events:
        # reassemble events dict into consistent form using Event objects as values
        events_dict = {}
        for event in events:
            obj = cls if event.attribute is None else getattr(cls, event.attribute)
            sqlalchemy.event.listen(obj, event.name, event.listener, **event.kargs)
            events_dict.setdefault(event.name, []).append(event)

        dct['__events__'].update(events_dict)

#####
## Event decorators
####

def event(event_name, attribute=None, f=None, **event_kargs):
    '''
    Generic event decorator maker which attaches metadata to function object
    so that `register()` can find the event definition.
    '''
    if callable(f):
        # being called as a decorator with no arguments
        return event(event_name)(f)

    def decorator(f):
        if not hasattr(f, '__event__'):
            # set initial value to list so a function can handle multiple events
            f.__event__ = []

        # Attach event object to function which will be picked up in `register()`.
        f.__event__.append(Event(event_name, attribute, f, event_kargs))

        # Return function as-is since method definition should be compatible with sqlalchemy.event.listen().
        return f
    return decorator

##
# Attribute Events
# http://docs.sqlalchemy.org/en/latest/orm/events.html#attribute-events
##

set_ = partial(event, 'set')
append = partial(event, 'append')
remove = partial(event, 'remove')

##
# Mapper Events
# http://docs.sqlalchemy.org/en/latest/orm/events.html#mapper-events
##

before_delete = partial(event, 'before_delete', None)
before_insert = partial(event, 'before_insert', None)
before_update = partial(event, 'before_update', None)

after_delete = partial(event, 'after_delete', None)
after_insert = partial(event, 'after_insert', None)
after_update = partial(event, 'after_update', None)

append_result = partial(event, 'append_result', None)
create_instance = partial(event, 'create_instance', None)
instrument_class = partial(event, 'instrument_class', None)
before_configured = partial(event, 'before_configured', None)
after_configured = partial(event, 'after_configured', None)
mapper_configured = partial(event, 'mapper_configured', None)
populate_instance = partial(event, 'populate_instance', None)
translate_row = partial(event, 'translate_row', None)

##
# Instance Events
# http://docs.sqlalchemy.org/en/latest/orm/events.html#instance-events
##

expire = partial(event, 'expire', None)
load = partial(event, 'load', None)
refresh = partial(event, 'refresh', None)

# The following events work as intended, but they don't seem like
# likely candidates for supporting their definition on the model class.

# @why: Having an on-some-init event defined on the model class
# seems inefficient since whatever logic they contain should be
# handled in model.__init__() anyway.
#first_init = partial(event, 'first_init', None)
#init = partial(event, 'init', None)
#init_failure = partial(event, 'init_failure', None)

# @why: Again model class would already define pickle support
# so logic should be contained there and not in a separate event handler.
#pickle = partial(event, 'pickle', None)
#unpickle = partial(event, 'unpickle', None)

# @why: Well, not really sure how to actually trigger this event
# so don't want to support it if it doesn't have a test.
# If someone really wants this event, then it can be enabled.
#resurrect = partial(event, 'resurrect', None)

