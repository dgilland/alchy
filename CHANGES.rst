Changelog
=========


v1.0.0 (2014-08-25)
-------------------

- Replace usage of ``@classproperty`` decorators in ``ModelBase`` with ``@classmethod``. Any previously defined class properties now require method access. Affected attributes are: ``session``, ``primary_key``, ``primary_keys``, ``primary_attrs``, ``attrs``, ``descriptors``, ``relationships``, ``column_attrs``, and ``columns``. (**breaking change**)
- Proxy ``getitem`` and ``setitem`` access to ``getattr`` and ``setattr`` in ``ModelBase``. Allows models to be accessed like dictionaries.
- Make ``alchy.events`` decorators class based.
- Require ``alchy.events`` decorators to be instantiated using a function call (e.g. ``@events.before_update()`` instead of ``@events.before_update``). (**breaking change**)
- Add ``alchy.search`` comparators, ``eqenum`` and ``noteqenum``, for comparing ``DeclarativeEnum`` types.


v0.13.3 (2014-07-26)
--------------------

- Fix ``utils.iterflatten()`` by calling ``iterflatten()`` instead of ``flatten`` in recursive loop.


v0.13.2 (2014-06-12)
--------------------

- Add ``ModelBase.primary_attrs`` class property that returns a list of class attributes that are primary keys.
- Use ``ModelBase.primary_attrs`` in ``QueryModel.search()`` so that it handles cases where primary keys have column names that are different than the class attribute name.


v0.13.1 (2014-06-11)
--------------------

- Modify internals of ``QueryModel.search()`` to better handle searching on a query object that already has joins and filters applied.


v0.13.0 (2014-06-03)
--------------------

- Add ``search.icontains`` and ``search.noticontains`` for case insensitive contains filter.
- Remove strict update support from ``Model.update()``. Require this to be implemented in user-land. (**breaking change**)


v0.12.0 (2014-05-18)
--------------------

- Merge originating query where clause in ``Query.search`` so that pagination works properly.
- Add ``session_class`` argument to ``Manager`` which can override the default session class used.


v0.11.3 (2014-05-05)
--------------------

- In ``ModelMeta`` when checking whether to do tablename autogeneration, tranverse all base classes when trying to determine if a primary key is defined.
- In ``ModelMeta`` set ``bind_key`` in ``__init__`` method instead of ``__new__``. This also fixes an issue where ``__table_args__`` was incorrectly assumed to always be a ``dict``.


v0.11.2 (2014-05-05)
--------------------

- Support ``order_by`` as list/tuple in ``QueryModel.search()``.


v0.11.1 (2014-05-05)
--------------------

- Fix bug in ``QueryModel.search()`` where ``order_by`` wasn't applied in the correct order. Needed to come before limit/offset are applied.


v0.11.0 (2014-05-04)
--------------------

- PEP8 compliance with default settings.
- Remove ``query_property`` argument from ``make_declarative_base()`` and ``extend_declarative_base()``. (**breaking change**)
- Add ``ModelBase.primary_keys`` class property which returns a tuple always (``ModelBase.primary_key`` returns a single key if only one present or a tuple if multiple).
- Move location of class ``QueryProperty`` from ``alchy.model`` to ``alchy.query``. (**breaking change**)
- Create new ``Query`` subclass named ``QueryModel`` which is to be used within a query property context. Replace ``Query`` with ``QueryModel`` as default query class. (**breaking change**)
- Move ``__advanced_search__`` and ``__simple_search__`` class attributes from ``ModelBase`` to ``QueryModel``. (**breaking change**)
- Introduce ``QueryModel.__search_filters__`` which can define a canonical set of search filters which can then be referenced in the list version of ``__advanced_search__`` and ``__simple_search__``.
- Modify the logic of ``QueryModel.search()`` to use a subquery joined onto the originating query in order to support pagination when one-to-many and many-to-many joins are present on the originating query. (**breaking change**)
- Support passing in a callable that returns a column attribute for ``alchy.search.<method>()``. Allows for ``alchy.search.contains(lambda: Foo.id)`` to be used at the class attribute level when ``Foo.id`` will be defined later.
- Add search operators ``any_/notany_`` and ``has/nothas`` which can be used for the corresponding relationship operators.


v0.10.0 (2014-04-02)
--------------------

- Issue warning instead of failing when installed version of SQLAlchemy isn't compatible with ``alchy.Query``'s loading API (i.e. missing ``sqlalchemy.orm.strategy_options.Load``). This allows ``alchy`` to be used with earlier versions of SQLAlchemy at user's own risk.
- Add ``alchy.search`` module which provides compatible search functions for ``ModelBase.__advanced_search__`` and ``ModelBase.__simple_search__``.


v0.9.1 (2014-03-30)
-------------------

- Change ``ModelBase.session`` to proxy ``ModelBase.query.session``.
- Add ``ModelBase.object_session`` proxy to ``orm.object_session(ModelBase)``.


v0.9.0 (2014-03-26)
-------------------

- Remove ``engine_config_prefix`` argument to ``Manager()``. (**breaking change**)
- Add explicit ``session_options`` argument to ``Manager()``. (**breaking change**)
- Change the ``Manager.config`` options to follow Flask-SQLAlchemy. (**breaking change**)
- Allow ``Manager.config`` to be either a ``dict``, ``class``, or ``module object``.
- Add multiple database engine support using a single ``Manager`` instance.
- Add ``__bind_key__`` configuration option for ``ModelBase`` for binding model to specific database bind (similar to Flask-SQLAlchemy).

v0.8.0 (2014-03-18)
-------------------

- For ``ModelBase.update()`` don't nest ``update()`` calls if field attribute is a ``dict``.
- Deprecated ``refresh_on_empty`` argument to ``ModelBase.to_dict()`` and instead implement ``ModelBase.__to_dict__`` configuration property as place to handle processing of model before casting to ``dict``. (**breaking change**)
- Add ``ModelBase.__to_dict__`` configuration property which handles preprocessing for model instance and returns a set of fields as strings to be used as dict keys when calling ``to_dict()``.


v0.7.0 (2014-03-13)
-------------------

- Rename ``alchy.ManagerBase`` to ``alchy.ManagerMixin``. (**breaking change**)
- Add ``pylint`` support.
- Remove dependency on ``six``.


v0.6.0 (2014-03-10)
-------------------

- Prefix event decorators which did not start with ``before_`` or ``after_`` with ``on_``. Specifically, ``on_set``, ``on_append``, ``on_remove``, ``on_append_result``, ``on_create_instance``, ``on_instrument_class``, ``on_mapper_configured``, ``on_populate_instance``, ``on_translate_row``, ``on_expire``, ``on_load``, and ``on_refresh``. (**breaking change**)
- Remove lazy engine/session initialization in ``Manager``. Require that ``Model`` and ``config`` be passed in at init time. While this removes some functionality, it's done to simplify the ``Manager`` code so that it's more straightforward. If lazy initialization is needed, then a proxy class should be used. (**breaking change**)


v0.5.0 (2014-03-02)
-------------------

- Add ``ModelBase.primary_key`` class property for retrieving primary key(s).
- Add ``Base=None`` argument to ``make_declarative_base()`` to support passing in a subclass of ``ModelBase``. Previously had to create a declarative ``Model`` to pass in a subclassed ``ModelBase``.
- Let any exception occurring in ``ModelBase.query`` attribute access bubble up (previously, ``UnmappedClassError`` was caught).
- Python 2.6 and 3.3 support.
- PEP8 compliance.
- New dependency: ``six`` (for Python 3 support)


v0.4.2 (2014-02-24)
-------------------

- In ``ModelBase.to_dict()`` only include fields which are mapper descriptors.
- Support ``to_dict`` method hook when iterating over objects in ``ModelBase.to_dict()``.
- Add ``to_dict`` method hook to ``EnumSymbol`` (propagates to ``DeclarativeEnum``).


v0.4.1 (2014-02-23)
-------------------

- Support ``__iter__`` method in model so that ``dict(model)`` is equilvalent to ``model.to_dict()``.
- Add ``refresh_on_empty=True`` argument to ``ModelBase.to_dict()`` which supports calling ``ModelBase.refresh()`` if ``__dict__`` is empty.


v0.4.0 (2014-02-23)
-------------------

- Add ``ModelBase.save()`` method which adds model instance loaded from session to transaction.
- Add ``ModelBase.get_by()`` which proxies to ``ModelBase.query.filter_by().first()``.
- Add model attribute ``events``.
- Add support for multiple event decoration.
- Add named events for all supported events.
- Add composite events for ``before_insert_update`` and ``after_insert_update``.


v0.3.0 (2014-02-07)
-------------------

- Rename ``ModelBase.advanced_search_config`` to ``ModelBase.__advanced_search__``.
- Rename ``ModelBase.simple_search_config`` to ``ModelBase.__simple_search__``
- Add ``ModelMeta`` metaclass.
- Implement ``__tablename__`` autogeneration from class name.
- Add mapper event support via ``ModelBase.__events__`` and/or ``model.event`` decorator.


v0.2.1 (2014-02-03)
-------------------

- Fix reference to ``model.make_declarative_base`` in ``Manager`` class.


v0.2.0 (2014-02-02)
-------------------

- Add default ``query_class`` to declarative model if none defined.
- Let ``model.make_declarative_base()`` accept predefined base and just extend its functionality.


v0.1.0 (2014-02-01)
-------------------

- First release
