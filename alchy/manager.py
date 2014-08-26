"""Manager class and mixin.

The :class:`Manager` class helps manage a SQLAlchemy database session as well
as provide convenience functions for commons operations.


Configuration
-------------

The following configuration values can be passed into a new :class:`Manager`
instance as a ``dict``, ``class``, or ``module``.

===========================  ==================================================
``SQLALCHEMY_DATABASE_URI``  URI used to connect to the database. Defaults to
                             ``sqlite://``.
``SQLALCHEMY_BINDS``         A ``dict`` that maps bind keys to database URIs.
                             Optionally, in place of a database URI, a
                             configuration ``dict`` can be used to overrided
                             connection options.
``SQLALCHEMY_ECHO``          When ``True`` have SQLAlchemy echo all SQL
                             statements. Defaults to ``False``.
``SQLALCHEMY_POOL_SIZE``     The size of the database pool. Defaults to the
                             engine's default (usually ``5``).
``SQLALCHEMY_POOL_TIMEOUT``  Specifies the connection timeout for the pool.
                             Defaults to ``10``.
``SQLALCHEMY_POOL_RECYCLE``  Number of seconds after which a connection is
                             automatically recycled.
``SQLALCHEMY_MAX_OVERFLOW``  Controls the number of connections that can be
                             created after the pool reached its maximum size.
                             When those additional connections are returned to
                             the pool, they are disconnected and discarded.
===========================  ==================================================
"""

from functools import partial

import sqlalchemy
from sqlalchemy import orm
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm.exc import UnmappedError

from .model import make_declarative_base, extend_declarative_base
from .query import QueryModel
from .session import Session
from ._compat import string_types, itervalues


__all__ = [
    'ManagerMixin',
    'Manager',
    'Config',
]


class ManagerMixin(object):
    """Extensions for :attr:`Manager.session`."""

    def add(self, *instances):
        """Override ``session.add()`` so it can function like
        ``session.add_all()``.

        Note:
            Supports chaining.
        """
        for instance in instances:
            if isinstance(instance, list):
                self.add(*instance)
            else:
                self.session.add(instance)
        return self.session

    def add_commit(self, *instances):
        """Add instances to session and commit in one call."""
        self.add(*instances).commit()

    def delete(self, *instances):
        """Override ``session.delete()`` so it can function like
        ``session.add_all()``.

        Note:
            Supports chaining.
        """
        for instance in instances:
            if isinstance(instance, list):
                self.delete(*instance)
            else:
                self.session.delete(instance)
        return self.session

    def delete_commit(self, *instances):
        """Delete instances to session and commit in one call."""
        self.delete(*instances).commit()


class Manager(ManagerMixin):
    """Manager class for database session.

    Initialization of :class:`Manager` accepts a config object, session
    options, and an optional declarative base. If ``Model`` isn't provided,
    then a default one is generated using
    :func:`alchy.model.make_declarative_base`. The declarative base model is
    accessible at :attr:`Model`.

    By default the ``session_options`` are::

        {
            'query_cls': alchy.Query,
            'autocommit': False,
            'autoflush': True
        }

    The default :attr:`session_class` is :class:`alchy.Session`. If you want to
    provide your own session class, then it's suggested that you subclass
    :class:`alchy.Session` and pass it in via :attr:`session_class`. This way
    your subclass will inherit the functionality of :class:`alchy.Session`.
    """

    def __init__(self,
                 config=None,
                 session_options=None,
                 Model=None,
                 session_class=None):

        #: Database engine configuration options.
        self.config = Config(defaults={
            'SQLALCHEMY_DATABASE_URI': 'sqlite://',
            'SQLALCHEMY_BINDS': None,
            'SQLALCHEMY_ECHO': False,
            'SQLALCHEMY_POOL_SIZE': None,
            'SQLALCHEMY_POOL_TIMEOUT': None,
            'SQLALCHEMY_POOL_RECYCLE': None,
            'SQLALCHEMY_MAX_OVERFLOW': None
        })

        if isinstance(config, dict):
            self.config.update(config)
        elif config is not None:
            self.config.from_object(config)

        self._engines = {}
        self._binds = {}

        if session_options is None:
            session_options = {}

        session_options.setdefault('query_cls', QueryModel)
        session_options.setdefault('autocommit', False)
        session_options.setdefault('autoflush', True)

        #: Class to used for session object.
        self.session_class = session_class or Session

        #: Scoped session object.
        self.session = self.create_scoped_session(session_options)

        if Model is None:
            #: Declarative base model class.
            self.Model = make_declarative_base()
        else:
            self.Model = Model

        if self.Model:
            extend_declarative_base(self.Model, self.session)

    @property
    def metadata(self):
        """Return :attr:`Model` metadata object."""
        return getattr(self.Model, 'metadata', None)

    @property
    def binds(self):
        """Returns config options for all binds."""
        if not self._binds:
            self._binds = {
                None: self.config['SQLALCHEMY_DATABASE_URI']
            }

            if self.config['SQLALCHEMY_BINDS']:
                self._binds.update(self.config['SQLALCHEMY_BINDS'])

        return self._binds

    @property
    def binds_map(self):
        """Returns a dictionary with a table->engine mapping. This is suitable
        for use in ``sessionmaker(binds=binds_map)``.
        """
        binds = list(self.binds)
        retval = {}
        for bind in binds:
            engine = self.get_engine(bind)
            tables = self.get_tables_for_bind(bind)
            retval.update(dict((table, engine) for table in tables))
        return retval

    @property
    def engine(self):
        """Return default database engine."""
        return self.get_engine()

    def create_engine(self, uri_or_config):
        """Create engine using either a URI or a config dict. If URI supplied,
        then the default :attr:`config` will be used. If config supplied, then
        URI in config will be used.
        """
        if isinstance(uri_or_config, dict):
            uri = uri_or_config['SQLALCHEMY_DATABASE_URI']
            config = uri_or_config
        else:
            uri = uri_or_config
            config = self.config

        options = engine_options_from_config(config)

        return sqlalchemy.create_engine(make_url(uri), **options)

    def get_engine(self, bind=None):
        """Return engine associated with bind. Create engine if it doesn't
        already exist.
        """
        if bind not in self._engines:
            assert bind in self.binds, (
                'Bind {0} is not specified. '
                'Set in SQLALCHEMY_BINDS configuration variable'.format(bind))

            self._engines[bind] = self.create_engine(self.binds[bind])

        return self._engines[bind]

    def create_scoped_session(self, options=None):
        """Create scoped session which internally calls :meth:`create_session`.
        """
        if options is None:  # pragma: no cover
            options = {}
        return orm.scoped_session(partial(self.create_session, options))

    def create_session(self, options):
        """Create session instance using custom Session class that supports
        multiple bindings.
        """
        return self.session_class(self, **options)

    def get_tables_for_bind(self, bind=None):
        """Returns a list of all tables relevant for a bind."""
        return [table
                for table in itervalues(self.metadata.tables)
                if table.info.get('bind_key') == bind]

    def _execute_for_all_tables(self, bind, operation, skip_tables=False):
        """Execute metadata operation for associated tables."""
        if self.metadata is None:
            raise UnmappedError('Missing declarative base model')

        if bind == '__all__':
            binds = [None] + list(self.config.get('SQLALCHEMY_BINDS') or {})
        elif isinstance(bind, string_types) or bind is None:
            binds = [bind]
        else:
            binds = bind

        for bind in binds:
            extra = {}
            if not skip_tables:
                tables = self.get_tables_for_bind(bind)
                extra['tables'] = tables
            metadata_operation = getattr(self.metadata, operation)
            metadata_operation(bind=self.get_engine(bind), **extra)

    def create_all(self, bind='__all__'):
        """Create database schema from models."""
        self._execute_for_all_tables(bind, 'create_all')

    def drop_all(self, bind='__all__'):
        """Drop tables defined by models."""
        self._execute_for_all_tables(bind, 'drop_all')

    def reflect(self, bind='__all__'):
        """Reflect tables from database."""
        self._execute_for_all_tables(bind, 'reflect', skip_tables=True)

    def __getattr__(self, attr):
        """Delegate all other attributes to :attr:`session`."""
        return getattr(self.session, attr)


class Config(dict):
    """Configuration loader which acts like a dict but supports loading
    values from an object limited to ``ALL_CAPS_ATTRIBUTES``.
    """
    def __init__(self, defaults=None):
        super(Config, self).__init__(defaults or {})

    def from_object(self, obj):
        """Pull ``dir(obj)`` keys from `obj` and set onto ``self``."""
        for key in dir(obj):
            if key.isupper():
                self[key] = getattr(obj, key)


def engine_options_from_config(config):
    """Return engine options derived from config object."""
    options = {}

    def _setdefault(optionkey, configkey):
        """Set options key if config key is not None."""
        if config.get(configkey) is not None:
            options[optionkey] = config[configkey]

    _setdefault('echo', 'SQLALCHEMY_ECHO')
    _setdefault('pool_size', 'SQLALCHEMY_POOL_SIZE')
    _setdefault('pool_timeout', 'SQLALCHEMY_POOL_TIMEOUT')
    _setdefault('pool_recycle', 'SQLALCHEMY_POOL_RECYCLE')
    _setdefault('max_overflow', 'SQLALCHEMY_MAX_OVERFLOW')

    return options
