## vX.X.X

- Add `ModelBase.save()` method which adds model instance loaded from session to transaction.
- Add `ModelBase.get_by()` which proxies to `ModelBase.query.filter_by().first()`.

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
