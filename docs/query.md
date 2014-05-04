# QueryModel

The default query class used for ORM queries when accessing `manager.query`, `manager.session.query`, or `SomeModel.query`. Can be used in other libraries/implementations when creating a session.

```python
from sqlalchemy import orm

from alchy import QueryModel
# or if not using as query property
# from alchy import Query


session = orm.scoped_session(orm.sessionmaker())
session.configure(query_cls=QueryModel)
```

**NOTE:** If you don't plan to use the query class as a query property, then you can use the `Query` class instead since it won't include features that only work within a query property context.

## Methods

### map()

Call `map()` on query results.

```python
QueryModel.map(function, *iterable_args)

Model.query.map(lambda model: model.name)
```

### reduce()

Call `reduce()` on query results.

```python
QueryModel.reduce(function, initial=None)

Model.query.reduce(lambda result, i: result + i.number, 0)
```

### reduce_right()

Call `reduce()` on query results in reverse order.

```python
QueryModel.reduce_right(function, initial=None)

Model.query.reduce_right(lambda result, i: (i.number * result) + 1, 1)
```

### pluck()

Pluck field value from each row and return as a list.

```python
QueryModel.pluck(column)

Model.query.pluck('name')
```

### page()

Return a specific page of query results. Pages are 1-indexed.

```python
QueryModel.page(page=1, per_page=None)

# if `per_page` is None, then QueryModel.DEFAULT_PER_PAGE is used
Model.query.page(3) == Model.query.page(3, QueryModel.DEFAULT_PER_PAGE)

Model.query.page(3, 25)
```

### paginate()

Return a pagination object from query results (borrowed heavily from [Flask-SQLAlchemy](http://pythonhosted.org/Flask-SQLAlchemy/api.html#flask.ext.sqlalchemy.BaseQuery.paginate)).

```python
QueryModel.paginate(page=1, per_page=None, error_out=True)

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

### search()

There are two flavors of searching supported: simple and advanced. Simple search is similar to a Google search where the search terms are applied to multiple database fields simultaneously. Advanced search is named parameter searching where a search term is applied to a specific database field only.

Search currently only works within a query property context and requires that the Model's `query_class` attribute be set to a custom class derived from `QueryModel`.

To configure search, define the `__search_filters__` dict which contains the available filter expression functions and `__simple_search__` and/or `__advanced_search__` lists. Or alternatively `__simple_search__` and `__advanced_search__` can be defined as dicts which match the structure of `__search_filters__`.

```python
class Model1Query(QueryModel):
    __search_filters__ = {
        'model1_column1': lambda value: Model1.column1.contains(value),
        'model1_column2': lambda value: Model1.column2.contains(value),
        'model1_column3': lambda value: Model1.column3 == value
    }

    # List items should correspond to __search_filters__ keys.
    __advanced_search__ = ['model1_column3']
    __simple_search__ = ['model1_column1', 'model1_column2']

    # Or alternatively using dicts.
    #__advanced_search__ = {
    #    'model1_column3': lambda value: Model1.column3 == value
    #}
    #__simple_search__ = {
    #    'model1_column1': lambda value: Model1.column1.contains(value),
    #    'model1_column2': lambda value: Model1.column2.contains(value)
    #}
```

Given, the above query class, to perform an advanced search:

```python
# Find all records where Model1.column3 == 5.
Model1.query.search(search_dict={'model1_column3': 5})
```

To perform a simple search:

```python
# Find all records where "foo" and "bar" are contained in
# either Model1.column1 or Model1.column2.
Model1.query.search(search_string='foo bar')
```

Other options include `limit`, `offset`, and `order_by`.

**NOTE:** The `order_by` only applies to the subquery used for searching and not the final query returned. Due to the requirement that `search()` needs to support pagination on joins containing one-to-many and many-to-many relationships, all search filtering, pagination, and ordering is contained in a subquery which is then joined to the originating query.

```python
QueryModel.search(search_string=None, search_dict=None,
                  limit=None, offset=None, order_by=None)
```

## Entity Load Methods

The following methods curry functional loading methods onto the query object to make it easier to apply various join methods with query options. For more details on SQLAlchemy's Loader API see [Relationship Loading Techniques](http://docs.sqlalchemy.org/en/latest/orm/loading.html).

### join_eager()

Join models using `orm.contains_eager` option.

```python
QueryModel.join_eager(*keys, **contains_eager_options)

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

Model1.query.join_eager(Model1.relation_1_to_2, Model2.relation_2_to_3)
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
QueryModel.joinedload(*keys, **joinedload_options)

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
QueryModel.immediateload(*keys, **immediateload_options)

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
QueryModel.lazyload(*keys, **lazyload_options)

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
QueryModel.noload(*keys, **noload_options)

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
QueryModel.subqueryload(*keys, **subqueryload_options)

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

Apply `Load.load_only()` to query. Arguments to `QueryModel.load_only` can be either all strings or an object with a `Load` API followed by strings.

```python
QueryModel.load_only(*columns)

Model1.query.load_only('_id', 'name')
Model1.query.join(Model2).load_only(Model1, 'name').load_only(Model2, 'name')
```

### defer()

Apply `Load.defer()` to query.

```python
QueryModel.defer(*columns)

Model1.query.defer('name', 'rank')
Model1.query.defer(Model1, 'name', 'rank')
Model1.query.lazyload(Model1.model2).defer(Model1.model2, 'name')
```

### undefer()

Apply `Load.undefer()` to query. Typically only used when a column was created using `orm.deferred()` as in `name = orm.deferred(Column(types.String()))`

```python
QueryModel.undefer(*columns)

Model1.query.undefer('name', 'rank')
Model1.query.undefer(Model1, 'name', 'rank')
Model1.query.join_eager(Model1.model2).undefer(Model1.model2, 'name')
```

### undefer_group()

Apply `Load.undefer_group()` to query. Requires `group` argument used when calling `orm.deferred()` as in `name = orm.deferred(Column(types.String()), group='deferred')`

```python
QueryModel.undefer(*columns)

Model1.query.undefer_group('deferred_model1')
Model1.query.undefer_group(Model1, 'deferred_model1')
Model1.query.lazyload(Model1.model2).undefer('deferred_model2')
```
