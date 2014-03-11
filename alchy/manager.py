'''Manager class and mixin.

Provides `Manager` class for interacting with a database session via SQLAlchemy's orm.scoped_session.
'''

from sqlalchemy import engine_from_config, orm
from sqlalchemy.orm.exc import UnmappedError

from alchy import query, model


class ManagerMixin(object):
    '''Useful extensions to self.session.'''

    def add(self, *instances):
        '''Override `session.add()` so it can function like `session.add_all()` and support chaining.'''
        for instance in instances:
            if isinstance(instance, list):
                self.add(*instance)
            else:
                self.session.add(instance)
        return self.session

    def add_commit(self, *instances):
        '''Add instances to session and commit in one call.'''
        self.add(*instances).commit()

    def delete(self, *instances):
        '''Override `session.delete()` so it can function like `session.add_all()` and support chaining.'''
        for instance in instances:
            if isinstance(instance, list):
                self.delete(*instance)
            else:
                self.session.delete(instance)
        return self.session

    def delete_commit(self, *instances):
        '''Delete instances to session and commit in one call.'''
        self.delete(*instances).commit()


class Manager(ManagerMixin):
    '''Manager for session.'''

    def __init__(self, config, Model=None, engine_config_prefix=''):
        self.Model = model.make_declarative_base() if Model is None else Model
        self.config = config

        engine_config = self.config['engine']

        self.engine = engine_from_config(engine_config, prefix=engine_config_prefix)

        session_config = self.config.get('session', {})
        session_config['bind'] = self.engine
        session_config.setdefault('autocommit', False)
        session_config.setdefault('autoflush', True)
        session_config.setdefault('query_cls', query.Query)

        self.session = orm.scoped_session(orm.sessionmaker())
        self.session.configure(**session_config)

        if self.Model:
            model.extend_declarative_base(self.Model, self.session)

    @property
    def metadata(self):
        '''Return `Model`'s metadata object.'''
        return getattr(self.Model, 'metadata', None)

    def create_all(self):
        '''Create database schema from models.'''
        if self.metadata is None:
            raise UnmappedError('Missing declarative base model')
        self.metadata.create_all(bind=self.engine)

    def drop_all(self):
        '''Drop tables defined by models.'''
        if self.metadata is None:
            raise UnmappedError('Missing declarative base model')
        self.metadata.drop_all(bind=self.engine)

    def __getattr__(self, attr):
        '''Delegate all other attributes to self.session.'''
        return getattr(self.session, attr)
