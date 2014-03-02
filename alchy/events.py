
from functools import wraps, partial
from collections import namedtuple

import sqlalchemy
import six

Event = namedtuple('Event', ['name', 'attribute', 'listener', 'kargs'])


def register(cls, dct):
    events = []

    # append class attribute defined events
    if dct.get('__events__'):
        # events defined on __events__ can have many forms (e.g. string based, list of tuples, etc)
        # so we need to iterate over them and parse into standardized Event object
        for event_name, listeners in six.iteritems(dct['__events__']):
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
            if not isinstance(value.__event__, list):  # pragma: no cover
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


def event(event_names, attribute=None, f=None, **event_kargs):
    '''
    Generic event decorator maker which attaches metadata to function object
    so that `register()` can find the event definition.
    '''
    if callable(f):
        # being called as a decorator with no arguments
        return event(event_names)(f)

    def decorator(f):
        if not hasattr(f, '__event__'):
            # set initial value to list so a function can handle multiple events
            f.__event__ = []

        # @note: have to assign to a separately variable name due to global name access issues
        if not isinstance(event_names, (list, tuple)):
            _event_names = [event_names]
        else:
            _event_names = event_names

        # Attach event object to function which will be picked up in `register()`.
        f.__event__ += [Event(event_name, attribute, f, event_kargs) for event_name in _event_names]

        # Return function as-is since method definition should be compatible with sqlalchemy.event.listen().
        return f
    return decorator


def make_attribute_event(event_names):
    '''Event decorator maker for attribute events.'''
    return partial(event, event_names)


def make_event(event_names):
    '''Event decorator maker for mapper or instance events which don't require an attribute.'''
    # bind `None` to attribute argument
    return partial(event, event_names, None)

##
# Attribute Events
# http://docs.sqlalchemy.org/en/latest/orm/events.html#attribute-events
##

set_ = make_attribute_event('set')
append = make_attribute_event('append')
remove = make_attribute_event('remove')

##
# Mapper Events
# http://docs.sqlalchemy.org/en/latest/orm/events.html#mapper-events
##

before_delete = make_event('before_delete')
before_insert = make_event('before_insert')
before_update = make_event('before_update')
before_insert_update = make_event(['before_insert', 'before_update'])

after_delete = make_event('after_delete')
after_insert = make_event('after_insert')
after_update = make_event('after_update')
after_insert_update = make_event(['after_insert', 'after_update'])

append_result = make_event('append_result')
create_instance = make_event('create_instance')
instrument_class = make_event('instrument_class')
before_configured = make_event('before_configured')
after_configured = make_event('after_configured')
mapper_configured = make_event('mapper_configured')
populate_instance = make_event('populate_instance')
translate_row = make_event('translate_row')

##
# Instance Events
# http://docs.sqlalchemy.org/en/latest/orm/events.html#instance-events
##

expire = make_event('expire')
load = make_event('load')
refresh = make_event('refresh')

# The following events work as intended, but they don't seem like
# likely candidates for supporting their definition on the model class.

# @why: Having an on-some-init event defined on the model class
# seems inefficient since whatever logic they contain should be
# handled in model.__init__() anyway.
#first_init = make_event('first_init')
#init = make_event('init')
#init_failure = make_event('init_failure')

# @why: Again model class would already define pickle support
# so logic should be contained there and not in a separate event handler.
#pickle = make_event('pickle')
#unpickle = make_event('unpickle')

# @why: Well, not really sure how to actually trigger this event
# so don't want to support it if it doesn't have a test.
# If someone really wants this event, then it can be enabled.
#resurrect = make_event('resurrect')
