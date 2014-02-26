## vX.X.X (XXXX-XX-XX)

- Add `ModelBase.primary_key` class property for retrieving primary key(s).
- Add `Base=None` argument to `make_declarative_base()` to support passing in a subclass of `ModelBase`. Previously had to create a declarative `Model` to pass in a subclassed `ModelBase`.
- Add chaining support for `ModelBase` methods: `update`, `flush`, `save`, `expire`, `refresh`, and `expunge`.

## v0.4.2 (2014-02-24)

- In `ModelBase.to_dict()` only include fields which are mapper descriptors.
- Support `to_dict` method hook when iterating over objects in `ModelBase.to_dict()`.
- Add `to_dict` method hook to `EnumSymbol` (propagates to `DeclarativeEnum`).

## v0.4.1 (2014-02-23)

- Support `__iter__` method in model so that `dict(model)` is equilvalent to `model.to_dict()`.
- Add `refresh_on_empty=True` argument to `ModelBase.to_dict()` which supports calling `ModelBase.refresh()` if `__dict__` is empty.

## v0.4.0 (2014-02-23)

- Add `ModelBase.save()` method which adds model instance loaded from session to transaction.
- Add `ModelBase.get_by()` which proxies to `ModelBase.query.filter_by().first()`.
- Add model attribute `events`.
- Add support for multiple event decoration.
- Add named events for all supported events.
- Add composite events for `before_insert_update` and `after_insert_update`.

## v0.3.0 (2014-02-07)

- Rename `ModelBase.advanced_search_config` to `ModelBase.__advanced_search__`.
- Rename `ModelBase.simple_search_config` to `ModelBase.__simple_search__`
- Add `ModelMeta` metaclass.
- Implement `__tablename__` autogeneration from class name.
- Add mapper event support via `ModelBase.__events__` and/or `model.event` decorator.

## v0.2.1 (2014-02-03)

- Fix reference to `model.make_declarative_base` in `Manager` class.

## v0.2.0 (2014-02-02)

- Add default `query_class` to declarative model if none defined.
- Let `model.make_declarative_base()` accept predefined base and just extend its functionality.

## v0.1.0 (2014-02-01)

- First release
