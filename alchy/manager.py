
from sqlalchemy import engine_from_config, orm
from sqlalchemy.orm.exc import UnmappedError

from alchy import query, model


class ManagerBase(object):
    '''Useful extensions to self.session'''

    def add(self, *instances):
        '''Override `session.add()` so it can function like `session.add_all()` and support chaining'''
        for instance in instances:
            if isinstance(instance, list):
                self.add(*instance)
            else:
                self.session.add(instance)
        return self.session

    def add_commit(self, *instances):
        '''Add instances to session and commit in one call'''
        self.add(*instances).commit()

    def delete(self, *instances):
        '''Override `session.delete()` so it can function like `session.add_all()` and support chaining'''
        for instance in instances:
            if isinstance(instance, list):
                self.delete(*instance)
            else:
                self.session.delete(instance)
        return self.session

    def delete_commit(self, *instances):
        '''Delete instances to session and commit in one call'''
        self.delete(*instances).commit()


class Manager(ManagerBase):
    '''
    Manager for session
    '''
    def __init__(self, Model=None, config=None, session=None, engine=None):
        self.session = None

        # declarative base class
        self.Model = model.make_declarative_base() if Model is None else Model

        if config is None:
            config = {}

        self.init_session(config=config.get('session'), session=session)
        self.init_engine(config=config.get('engine'), engine=engine)

    def init_engine(self, config=None, engine=None, config_prefix=''):
        '''
        Initialize engine. Allow for lazy configuration after `__init__()`.
        If both `config` and `engine` are supplied, then the config generated engine will take precedence.
        New engine creation will also result in a new `session` object using `engine`.
        '''
        if config:
            engine = engine_from_config(config, prefix=config_prefix)

        self.init_session(config={'bind': engine})

    def init_session(self, config=None, session=None):
        '''
        Initialize session. Allow for lazy configuration after `__init__()`.
        If both `config` and `session` are supplied, `config` will configure `session`.
        '''
        self.session = session

        if self.session is None:
            self.session = orm.scoped_session(orm.sessionmaker())

        if config is None:
            config = {}

        config.setdefault('autocommit', False)
        config.setdefault('autoflush', True)
        config.setdefault('query_cls', query.Query)

        self.session.configure(**config)

        if self.Model:
            model.extend_declarative_base(self.Model, self.session)

    @property
    def metadata(self):
        return getattr(self.Model, 'metadata', None)

    @property
    def engine(self):
        return self.session.get_bind()

    def create_all(self):
        '''
        Creates database schema from models
        '''
        if self.metadata is None:
            raise UnmappedError('Missing declarative base model')
        self.metadata.create_all(bind=self.engine)

    def drop_all(self):
        '''
        Drops tables defined by models
        '''
        if self.metadata is None:
            raise UnmappedError('Missing declarative base model')
        self.metadata.drop_all(bind=self.engine)

    def __getattr__(self, attr):
        '''
        Delegate all other attributes to self.session
        '''
        return getattr(self.session, attr)
