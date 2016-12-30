"""Main package API entry point.

Import core objects here.
"""

from .__pkg__ import (
    __description__,
    __url__,
    __version__,
    __author__,
    __email__,
    __license__
)

from .model import ModelBase, make_declarative_base
from .query import Query, QueryModel
from .manager import Manager, ManagerMixin
from .session import Session

__all__ = [
    'ModelBase',
    'make_declarative_base',
    'Query',
    'QueryModel',
    'Manager',
    'ManagerMixin',
    'Session'
]
