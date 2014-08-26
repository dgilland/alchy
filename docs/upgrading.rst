.. _upgrading:

Upgrading
*********


To v1.0.0
=========

The ``@classproperty`` decorator has been eliminated and replaced with ``@classmethod`` in ``v1.0.0``. This means that the previous :class:`alchy.model.ModelBase` class properties must now be accessed via method calls:

- :meth:`alchy.model.ModelBase.session`
- :meth:`alchy.model.ModelBase.primary_key`
- :meth:`alchy.model.ModelBase.primary_keys`
- :meth:`alchy.model.ModelBase.primary_attrs`
- :meth:`alchy.model.ModelBase.attrs`
- :meth:`alchy.model.ModelBase.descriptors`
- :meth:`alchy.model.ModelBase.relationships`
- :meth:`alchy.model.ModelBase.column_attrs`
- :meth:`alchy.model.ModelBase.columns`
