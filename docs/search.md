# Model Search

The `alchy.search` module contains a collection of SQLAlchemy Column Operator factory functions which are meant to be used for [QueryModel.search](model.md#search). These functions are syntatic sugar to make it easier to define compatible search functions. However, due to the fact that a model's query class has to be defined before the model and given that the model column attributes need to be defined before using the search factories, there are two ways to use the search factories on the query class: (1) defining `__search_filters__` as a property that returns the filter dict or (2) passing in a callable that returns the column.

For example, without `alchy.search` one would define a `__search_filters__` similar to:

```python
class UserQuery(QueryModel):
    __search_filters = {
        'email': lambda value: User.email.like(value)
    }

class User(Model):
    query_class = UserQuery
    email = Column(types.String(100))
```

Using `alchy.search` the above becomes:

```python
from alchy import search

class UserQuery(QueryModel):
    @property
    def __search_filters__(self):
        return {
            'email': like(User.email)
        }

class User(Model):
    query_class = UserQuery
    email = Column(types.String(100))
```

Or if a callable is passed in:

```python
from alchy import search

class UserQuery(QueryModel):
    __search_filters__ = {
        'email': like(lambda: User.email)
    }

class User(Model):
    query_class = UserQuery
    email = Column(types.String(100))
```

The available `alchy.search` functions:

| Search Function | Equivalent Column Operator |
| --- | --- |
| `like()` | `Column.like()` |
| `notlike()` | `not_(Column.like())` |
| `ilike()` | `Column.ilike()` |
| `notilike()` | `not_(Column.ilike()` |
| `startswith()` | `Column.startswith()` |
| `notstartswith()` | `not_(Column.startswith())` |
| `endswith()` | `Column.endswith()` |
| `notendswith()` | `not_(Column.endswith())` |
| `contains()` | `Column.contains()` |
| `notcontains()` | `not_(Column.contains())` |
| `in_()` | `Column.in_()` |
| `notin_()` | `not_(Column.in_())` |
| `eq()` | `Column == value` |
| `noteq()` | `not_(Column == value)` |
| `gt()` | `Column > value` |
| `notgt()` | `not_(Column > value)` |
| `ge()` | `Column >= value` |
| `notge()` | `not_(Column >= value)` |
| `lt()` | `Column < value` |
| `notlt()` | `not_(Column < value)` |
| `le()` | `Column <= value` |
| `notle()` | `not_(Column <= value)` |
| `any_()` | `Relationship.column.any()` |
| `notany_()` | `not_(Relationship.column.any())` |
| `has()` | `Relationship.column.has()` |
| `nothas()` | `not_(Relationship.column.has())` |

The call signature for the `search` functions is:

```python
# search.<function>(column)
# e.g.
search.contains(email)
```
