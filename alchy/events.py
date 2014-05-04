"""Declarative ORM event decorators and event registration.
"""

from functools import partial
from collections import namedtuple

import sqlalchemy

from ._compat import iteritems


Event = namedtuple('Event', ['name', 'attribute', 'listener', 'kargs'])


def register(cls, dct):
    """Register events defined on a class during metaclass creation."""

    events = []

    # append class attribute defined events
    if dct.get('__events__'):
        # Events defined on __events__ can have many forms (e.g. string based,
        # list of tuples, etc). So we need to iterate over them and parse into
        # standardized Event object.
        for event_name, listeners in iteritems(dct['__events__']):
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

                events.append(Event(
                    event_name, kargs.pop('attribute', None), listener, kargs))

    # add events which were added via @event decorator
    for value in dct.values():
        if hasattr(value, '__event__'):
            if not isinstance(value.__event__, list):  # pragma: no cover
                value.__event__ = [value.__event__]
            events.extend(value.__event__)

    if events:
        # Reassemble events dict into consistent form using Event objects as
        # values.
        events_dict = {}
        for evt in events:
            if evt.attribute is None:
                obj = cls
            else:
                obj = getattr(cls, evt.attribute)

            if evt.name.startswith('on_'):
                event_name = evt.name.replace('on_', '', 1)
            else:
                event_name = evt.name

            sqlalchemy.event.listen(obj, event_name, evt.listener, **evt.kargs)
            events_dict.setdefault(evt.name, []).append(evt)

        dct['__events__'].update(events_dict)


#####
# Event decorators
####


def event(event_names, attribute=None, no_args_func=None, **event_kargs):
    """Generic event decorator maker which attaches metadata to function object
    so that `register()` can find the event definition.
    """
    if callable(no_args_func):
        # being called as a decorator with no arguments
        return event(event_names)(no_args_func)

    def decorator(func):
        """Function decorator that attaches an `__event__` attribute hook which
        is expected when registering a method as an event handler. See
        `register()` in this module for details on how this is implemented.
        """
        if not hasattr(func, '__event__'):
            # Set initial value to list so function can handle multiple events.
            func.__event__ = []

        # NOTE: Have to assign to a separate variable name due to global name
        # access issues.
        if not isinstance(event_names, (list, tuple)):
            _event_names = [event_names]
        else:
            _event_names = event_names

        # Attach event object to function which will be picked up in
        # `register()`.
        func.__event__ += [Event(event_name, attribute, func, event_kargs)
                           for event_name in _event_names]

        # Return function as-is since method definition should be compatible
        # with sqlalchemy.event.listen().
        return func
    return decorator


def make_attribute_event(event_names):
    """Event decorator maker for attribute events."""
    return partial(event, event_names)


def make_event(event_names):
    """Event decorator maker for mapper or instance events which don't require
    an attribute.
    """
    # bind `None` to attribute argument
    return partial(event, event_names, None)

##
# Attribute Events
# http://docs.sqlalchemy.org/en/latest/orm/events.html#attribute-events
##

on_set = make_attribute_event('set')
on_append = make_attribute_event('append')
on_remove = make_attribute_event('remove')

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

on_append_result = make_event('append_result')
on_create_instance = make_event('create_instance')
on_instrument_class = make_event('instrument_class')
before_configured = make_event('before_configured')
after_configured = make_event('after_configured')
on_mapper_configured = make_event('mapper_configured')
on_populate_instance = make_event('populate_instance')
on_translate_row = make_event('translate_row')

##
# Instance Events
# http://docs.sqlalchemy.org/en/latest/orm/events.html#instance-events
##

on_expire = make_event('expire')
on_load = make_event('load')
on_refresh = make_event('refresh')

# The following events work as intended, but they don't seem like
# candidates for supporting their definition on the model class.

# @why: Having an on-some-init event defined on the model class
# seems inefficient since whatever logic they contain should be
# handled in model.__init__() anyway.
# on_first_init = make_event('first_init')
# on_init = make_event('init')
# on_init_failure = make_event('init_failure')

# @why: Again model class would already define pickle support
# so logic should be contained there and not in a separate event handler.
# on_pickle = make_event('pickle')
# on_unpickle = make_event('unpickle')

# @why: Well, not really sure how to actually trigger this event
# so don't want to support it if it doesn't have a test.
# If someone really wants this event, then it can be enabled.
# on_resurrect = make_event('resurrect')
