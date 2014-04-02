
from sqlalchemy import not_

from alchy import search

from .base import TestBase
from .fixtures import Search


class TestSearch(TestBase):
    function_mapping = [
        ('like', 'like'),
        ('notlike', 'notlike'),
        ('ilike', 'ilike'),
        ('notilike', 'notilike'),
        ('endswith', 'endswith'),
        ('notendswith', (not_, 'endswith')),
        ('startswith', 'startswith'),
        ('notstartswith', (not_, 'startswith')),
        ('contains', 'contains'),
        ('notcontains', (not_, 'contains')),
        ('eq', '__eq__'),
        ('noteq', (not_, '__eq__')),
        ('gt', '__gt__'),
        ('notgt', (not_, '__gt__')),
        ('ge', '__ge__'),
        ('notge', (not_, '__ge__')),
        ('lt', '__lt__'),
        ('notlt', (not_, '__lt__')),
        ('le', '__le__'),
        ('notle', (not_, '__le__')),
        ('in_', 'in_'),
        ('notin_', 'notin_')
    ]

    def test_search_functions(self):
        value = 'foo'

        for search_name, column_operator in self.function_mapping:
            search_func = getattr(search, search_name)(Search.string)

            if isinstance(column_operator, tuple):
                negate, column_operator = column_operator
            else:
                negate = None

            operator_func = getattr(Search.string, column_operator)
            operator_expression = operator_func(value)

            if negate:
                operator_expression = negate(operator_expression)

            self.assertEqual(
                str(search_func(value)),
                str(operator_expression)
            )
