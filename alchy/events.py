"""Declarative ORM event decorators and event registration.

SQLAlchemy features an ORM event API but one thing that is lacking is a way to
register event handlers in a declarative way inside the Model's class
definition. To bridge this gap, this module contains a collection of decorators
that enable this kind of functionality.

Instead of having to write event registration like this::

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
    event.listen(User, 'before_insert', before_insert_listener)

Model Events allows one to write event registration more succinctly as::

    from alchy import events

    from project.core import Model

    class User(Model):
        _id = Column(types.Integer(), primary_key=True)
        email = Column(types.String())

        @events.on_set('email', retval=True)
        def on_set_email(target, value, oldvalue, initiator):
            print 'received set event for target: {0}'.format(target)
            return value

        @events.before_insert()
        def before_insert(mapper, connection, target):
            print ('received "before_insert" event for target: {0}'
                   .format(target))

For details on each event type's expected function signature, see
`SQLAlchemy's ORM Events
<http://docs.sqlalchemy.org/en/latest/orm/events.html>`_.
"""
# pylint: disable=invalid-name

import sqlalchemy

from ._compat import iteritems


__all__ = [
    'on_set',
    'on_append',
    'on_remove',
    'before_delete',
    'before_insert',
    'before_update',
    'before_insert_update',
    'after_delete',
    'after_insert',
    'after_update',
    'after_insert_update',
    'on_append_result',
    'on_create_instance',
    'on_instrument_class',
    'before_configured',
    'after_configured',
    'on_mapper_configured',
    'on_populate_instance',
    'on_translate_row',
    'on_expire',
    'on_load',
    'on_refresh'
]


class Event(object):
    """Universal event class used when registering events."""
    def __init__(self, name, attribute, listener, kargs):
        self.name = name
        self.attribute = attribute
        self.listener = listener
        self.kargs = kargs


class GenericEvent(object):
    """Base class for generic event decorators."""
    event_names = None

    def __init__(self, **event_kargs):
        self.attribute = None
        self.event_kargs = event_kargs

    def __call__(self, func):
        return make_event(self.event_names,
                          self.attribute,
                          **self.event_kargs)(func)


class AttributeEvent(GenericEvent):
    """Base class for an attribute event decorators."""
    def __init__(self, attribute, **event_kargs):
        self.attribute = attribute
        self.event_kargs = event_kargs


##
# Attribute Events
# http://docs.sqlalchemy.org/en/latest/orm/events.html#attribute-events
##


class on_set(AttributeEvent):
    """Event decorator for the ``set`` event."""
    event_names = 'set'


class on_append(AttributeEvent):
    """Event decorator for the ``append`` event."""
    event_names = 'append'


class on_remove(AttributeEvent):
    """Event decorator for the ``remove`` event."""
    event_names = 'remove'


##
# Mapper Events
# http://docs.sqlalchemy.org/en/latest/orm/events.html#mapper-events
##


class before_delete(GenericEvent):
    """Event decorator for the ``before_delete`` event."""
    event_names = 'before_delete'


class before_insert(GenericEvent):
    """Event decorator for the ``before_insert`` event."""
    event_names = 'before_insert'


class before_update(GenericEvent):
    """Event decorator for the ``before_update`` event."""
    event_names = 'before_update'


class before_insert_update(GenericEvent):
    """Event decorator for the ``before_insert`` and ``before_update`` events.
    """
    event_names = ['before_insert', 'before_update']


class after_delete(GenericEvent):
    """Event decorator for the ``after_delete`` event."""
    event_names = 'after_delete'


class after_insert(GenericEvent):
    """Event decorator for the ``after_insert`` event."""
    event_names = 'after_insert'


class after_update(GenericEvent):
    """Event decorator for the ``after_update`` event."""
    event_names = 'after_update'


class after_insert_update(GenericEvent):
    """Event decorator for the ``after_insert`` and ``after_update`` events."""
    event_names = ['after_insert', 'after_update']


class on_append_result(GenericEvent):
    """Event decorator for the ``append_result`` event."""
    event_names = 'append_result'


class on_create_instance(GenericEvent):
    """Event decorator for the ``create_instance`` event."""
    event_names = 'create_instance'


class on_instrument_class(GenericEvent):
    """Event decorator for the ``instrument_class`` event."""
    event_names = 'instrument_class'


class before_configured(GenericEvent):
    """Event decorator for the ``before_configured`` event."""
    event_names = 'before_configured'


class after_configured(GenericEvent):
    """Event decorator for the ``after_configured`` event."""
    event_names = 'after_configured'


class on_mapper_configured(GenericEvent):
    """Event decorator for the ``mapper_configured`` event."""
    event_names = 'mapper_configured'


class on_populate_instance(GenericEvent):
    """Event decorator for the ``populate_instance`` event."""
    event_names = 'populate_instance'


class on_translate_row(GenericEvent):
    """Event decorator for the ``translate_row`` event."""
    event_names = 'translate_row'


##
# Instance Events
# http://docs.sqlalchemy.org/en/latest/orm/events.html#instance-events
##


class on_expire(GenericEvent):
    """Event decorator for the ``expire`` event."""
    event_names = 'expire'


class on_load(GenericEvent):
    """Event decorator for the ``load`` event."""
    event_names = 'load'


class on_refresh(GenericEvent):
    """Event decorator for the ``refresh`` event."""
    event_names = 'refresh'


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

                events.append(Event(event_name,
                                    kargs.pop('attribute', None),
                                    listener,
                                    kargs))

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


def make_event(event_names, attribute=None, **event_kargs):
    """Generic event decorator maker which attaches metadata to function object
    so that :func:`register` can find the event definition.
    """
    def decorator(func):
        """Function decorator that attaches an `__event__` attribute hook which
        is expected when registering a method as an event handler. See
        :func:`register` for details on how this is implemented.
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
