'''Main package API entry point.

Import core objects here.
'''

from .model import ModelBase, make_declarative_base
from .query import Query
from .manager import Manager, ManagerMixin

__version__ = '0.8.0'
__author__ = 'Derrick Gilland <dgilland@gmail.com>'
__all__ = ['ModelBase', 'make_declarative_base', 'Query', 'Manager', 'ManagerMixin']
