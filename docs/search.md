# Model Search

The `alchy.search` module contains a collection of SQLAlchemy Column Operator factory functions which are meant to be used for [Model.\_\_advanced_search\_\_](model.md#9595advanced_search9595) and [Model.\_\_simple_search\_\_](model.md#9595simple_search9595). These functions are syntatic sugar to make it easier to define compatible search functions.

For example, without `alchy.search` one would define an `__advanced_search__` similar to:

```python
class User(Model):
	email = Column(types.String())

	__advanced_search__ = {
		'email': lambda value: User.email.contains(value)
	}
```

Using `alchy.search` the above becomes:

```python
from alchy import search

class User(Model):
	email = Column(types.String())

	__advanced_search__ = {
		'email': search.contains(email)
	}
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

The call signature for the `search` functions is:

```python
# search.<function>(column)
# e.g.
search.contains(email)
```
