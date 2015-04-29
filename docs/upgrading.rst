.. _upgrading:

Upgrading
*********


To v2.0.0
=========

The logic that sets a Model class' ``__table_args__`` and ``__mapper_args__`` (unless overridden in subclass) has been modified. A model's ``__local_table_args__`` and ``__local_mapper_args__`` are now merged with ``__global_table_args__`` and ``__global_mapper_args__`` from all classes in the class's ``mro()``. A ``__{global,local}_{table,mapper}_args__`` may be a callable or classmethod, in which case it is evaluated on the class whose ``__{table,mapper}_args__`` is being set.


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
