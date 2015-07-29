"""Session class that supports multiple database binds.
"""

from sqlalchemy.orm.session import Session as SessionBase


__all__ = [
    'Session'
]


class Session(SessionBase):
    """The default session used by :class:`alchy.manager.Manager`. It extends
    the default session system with bind selection.
    """

    def __init__(self, manager, **options):
        self.manager = manager
        bind = options.pop('bind', manager.engine)
        super(Session, self).__init__(bind=bind,
                                      binds=manager.binds_map,
                                      **options)

    def get_bind(self, mapper=None, clause=None):
        """Return engine bind using mapper info's bind_key if present."""
        # mapper is None if someone tries to just get a connection.
        if mapper is not None:
            info = getattr(mapper.mapped_table, 'info', {})
            bind_key = info.get('bind_key')

            if bind_key is not None:
                return self.manager.get_engine(bind=bind_key)

        return super(Session, self).get_bind(mapper, clause)
