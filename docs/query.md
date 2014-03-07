# Query

The default query class used for ORM queries when accessing `manager.query`, `manager.session.query`, or `SomeModel.query`. Can be used in other libraries/implementations when creating a session.

```python
from sqlalchemy import orm

from alchy import Query


session = orm.scoped_session(orm.sessionmaker())
session.configure(query_cls=Query)
```

## Methods

### map()

Call `map()` on query results.

```python
Query.map(function, *iterable_args)

Model.query.map(lambda model: model.name)
```

### reduce()

Call `reduce()` on query results.

```python
Query.reduce(function, initial=None)

Model.query.reduce(lambda result, i: result + i.number, 0)
```

### reduce_right()

Call `reduce()` on query results in reverse order.

```python
Query.reduce_right(function, initial=None)

Model.query.reduce_right(lambda result, i: (i.number * result) + 1, 1)
```

### pluck()

Pluck field value from each row and return as a list.

```python
Query.pluck(column)

Model.query.pluck('name')
```

### page()

Return a specific page of query results. Pages are 1-indexed.

```python
Query.page(page=1, per_page=None)

# if `per_page` is None, then Query.DEFAULT_PER_PAGE is used
Model.query.page(3) == Model.query.page(3, Query.DEFAULT_PER_PAGE)

Model.query.page(3, 25)
```

### paginate()

Return a pagination object from query results (borrowed heavily from [Flask-SQLAlchemy](http://pythonhosted.org/Flask-SQLAlchemy/api.html#flask.ext.sqlalchemy.BaseQuery.paginate)).

```python
Query.paginate(page=1, per_page=None, error_out=True)

page_3 = Model.query.paginate(3, per_page=25)

# assuming there's 100 total records
page_3.query == Model.query
page_3.page == 5
page_3.per_page == 25
page_3.pages == 4
page_3.total == 100

page_3.items == Model.query.page(5, 25)

page_3.prev_num == 4
page_3.next_num == 6
page_3.has_prev == True
page_3.has_next == True

page_2 = page_3.prev()
page_4 = page_3.next()
page_4.has_next == False
```

### advanced_search()

Perform an advanced search on all model entities contained in query. The `search_dict` provided are passed to all models via [Model.advanced_search()](model.md#advanced_search). The resulting filters (from all models) are ANDed together.

```python
Query.advanced_search(search_dict)

class Model1(Model):
    name = Column(types.String())

    __advanced_search__ = {
        'model1_name': lambda value: Model1.name.like('%{0}%'.format(value))
    }

class Model2(Model):
    name = Column(types.String())

    __advanced_search__ = {
        'model2_name': lambda value: Model1.name.like('%{0}%'.format(value))
    }

Model1.query.join(Model2).advanced_search({
    'model1_name': 'foo',
    'model2_name': 'bar'
})

# this is equivalent to the following query using core sqlalchemy
Model1.query.join(Model2).filter(
    and_(
        Model1.name.like('%{0}%').format('foo'),
        Model2.name.like('%{0}%').format('bar')
    )
)
```

To best support advanced searching when querying multiple models, it is recommended to namespace the `__advanced_search__` keys uniquely so that models having the same column attribute name can be queried individually.

### simple_search()

Perform a simple search on all model entities contained in query. The `search_string` provided are split on `space`. The resulting search terms are then passed to all models via [Model.simple_search()](model.md#simple_search) where each term is ORed together. Finally, the resulting filters (from all models) are ANDed together.

```python
Query.simple_search(search_string)

class Model1(Model):
    name = Column(types.String())

    __simple_search__ = {
        'name': lambda value: Model1.name.like('%{0}%'.format(value))
    }

class Model2(Model):
    name = Column(types.String())

    __simple_search__ = {
        'name': lambda value: Model1.name.like('%{0}%'.format(value))
    }

Model1.query.join(Model2).simple_search('foo bar')

# this is equivalent to the following query using core sqlalchemy
Model1.query.join(Model2).filter(
    and_(
        or_(
            Model1.name.like('%{0}%').format('foo'),
            Model1.name.like('%{0}%').format('bar')
        ),
        or_(
            Model2.name.like('%{0}%').format('foo'),
            Model2.name.like('%{0}%').format('bar')
        )
    )
)
```

### search()

Combine [Query.advanced_search()](#advanced_search) and [Query.simple_search()](#simple_search) into a single call. Optionally provide `limit` and `offset` parameters.

```python
Query.search(search_string=None, search_dict=None, limit=None, offset=None)

Model1.query.join(Model2).search('foo bar', {'model1': 'foo', 'model2': 'bar']})
```

## Entity Load Methods

The following methods curry functional loading methods onto the query object to make it easier to apply various join methods with query options.

### join_eager()

Join models using `orm.contains_eager` option.

```python
Query.join_eager(*keys, **contains_eager_options)

Model1.query.join_eager('relation_1_to_2')
# is equivalent to...
Model1.query.join('relation_1_to_2').options(
    orm.contains_eager('relation_1_to_2')
)

Model1.query.join_eager(Model1.relation_1_to_2)
# is equivalent to...
Model1.query.join(Model1.relation_1_to_2).options(
    orm.contains_eager(Model1.relation_1_to_2)
)

Model1.query.join_eager('relation_1_to_2', 'relation_2_to_3')
# is equivalent to...
Model1.query.join('relation_1_to_2', 'relation_2_to_3').options(
    orm.contains_eager('relation_1_to_2').contains_eager('relation_2_to_3')
)

Model1.query.join_eager('Model1.relation_1_to_2, Model2.relation_2_to_3)
# is equivalent to...
Model1.query.join(Model1.relation_1_to_2, Model2.relation_2_to_3).options(
    orm.contains_eager(Model1.relation_1_to_2).contains_eager(Model2.relation_2_to_3)
)
```

### outerjoin_eager()

Similar to [join_eager()](#join_eager) but using `outerjoin` instead of `join`.

### joinedload()

Apply `query.options(orm.joinedload())` to query.

```python
Query.joinedload(*keys, **joinedload_options)

Model1.query.joinedload(Model1.relation_1_to_2)
# is equivalent to...
Model1.query.options(
    orm.joinedload(Model1.relation_1_to_2)
)

Model1.query.joinedload(Model1.relation_1_to_2, Model2.relation_2_to_3)
# is equivalent to...
Model1.query.options(
    orm.joinedload(Model1.relation_1_to_2).joinedload(Model2.relation_2_to_3)
)
```

### immediateload()

Apply `query.options(orm.immediateload())` to query.

```python
Query.immediateload(*keys, **immediateload_options)

Model1.query.immediateload(Model1.relation_1_to_2)
# is equivalent to...
Model1.query.options(
    orm.immediateload(Model1.relation_1_to_2)
)

Model1.query.immediateload(Model1.relation_1_to_2, Model2.relation_2_to_3)
# is equivalent to...
Model1.query.options(
    orm.immediateload(Model1.relation_1_to_2).immediateload(Model2.relation_2_to_3)
)
```

### lazyload()

Apply `query.options(orm.lazyload())` to query.

```python
Query.lazyload(*keys, **lazyload_options)

Model1.query.lazyload(Model1.relation_1_to_2)
# is equivalent to...
Model1.query.options(
    orm.lazyload(Model1.relation_1_to_2)
)

Model1.query.lazyload(Model1.relation_1_to_2, Model2.relation_2_to_3)
# is equivalent to...
Model1.query.options(
    orm.lazyload(Model1.relation_1_to_2).lazyload(Model2.relation_2_to_3)
)
```

### noload()

Apply `query.options(orm.noload())` to query.

```python
Query.noload(*keys, **noload_options)

Model1.query.noload(Model1.relation_1_to_2)
# is equivalent to...
Model1.query.options(
    orm.noload(Model1.relation_1_to_2)
)

Model1.query.noload(Model1.relation_1_to_2, Model2.relation_2_to_3)
# is equivalent to...
Model1.query.options(
    orm.noload(Model1.relation_1_to_2).noload(Model2.relation_2_to_3)
)
```

### subqueryload()

Apply `query.options(orm.subqueryload())` to query.

```python
Query.subqueryload(*keys, **subqueryload_options)

Model1.query.subqueryload(Model1.relation_1_to_2)
# is equivalent to...
Model1.query.options(
    orm.subqueryload(Model1.relation_1_to_2)
)

Model1.query.subqueryload(Model1.relation_1_to_2, Model2.relation_2_to_3)
# is equivalent to...
Model1.query.options(
    orm.subqueryload(Model1.relation_1_to_2).subqueryload(Model2.relation_2_to_3)
)
```

## Column Load Methods

The following methods curry functional column loading methods onto the query object to make it easier to apply various column loading methods with query options.

### load_only()

Apply `Load.load_only()` to query. Arguments to `Query.load_only` can be either all strings or an object with a `Load` API followed by strings.

```python
Query.load_only(*columns)

Model1.query.load_only('_id', 'name')
Model1.query.join(Model2).load_only(Model1, 'name').load_only(Model2, 'name')
```

### defer()

Apply `Load.defer()` to query.

```python
Query.defer(*columns)

Model1.query.defer('name', 'rank')
Model1.query.defer(Model1, 'name', 'rank')
Model1.query.lazyload(Model1.model2).defer(Model1.model2, 'name')
```

### undefer()

Apply `Load.undefer()` to query. Typically only used when a column was created using `orm.deferred()` as in `name = orm.deferred(Column(types.String()))`

```python
Query.undefer(*columns)

Model1.query.undefer('name', 'rank')
Model1.query.undefer(Model1, 'name', 'rank')
Model1.query.join_eager(Model1.model2).undefer(Model1.model2, 'name')
```

### undefer_group()

Apply `Load.undefer_group()` to query. Requires `group` argument used when calling `orm.deferred()` as in `name = orm.deferred(Column(types.String()), group='deferred')`

```python
Query.undefer(*columns)

Model1.query.undefer_group('deferred_model1')
Model1.query.undefer_group(Model1, 'deferred_model1')
Model1.query.lazyload(Model1.model2).undefer('deferred_model2')
```
