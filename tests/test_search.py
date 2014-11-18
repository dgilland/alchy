
from sqlalchemy import not_

from alchy import search

from .base import TestBase
from .fixtures import Search, SearchOne, SearchMany, OrderStatus


class TestSearch(TestBase):
    value = 'p'

    def test_like(self):
        test = search.like(Search.string)(self.value)
        target = Search.string.like(self.value)

        self.assertEqual(str(test), str(target))

    def test_notlike(self):
        test = search.notlike(Search.string)(self.value)
        target = not_(Search.string.like(self.value))

        self.assertEqual(str(test), str(target))

    def test_ilike(self):
        test = search.ilike(Search.string)(self.value)
        target = Search.string.ilike(self.value)

        self.assertEqual(str(test), str(target))

    def test_notilike(self):
        test = search.notilike(Search.string)(self.value)
        target = not_(Search.string.ilike(self.value))

        self.assertEqual(str(test), str(target))

    def test_startswith(self):
        test = search.startswith(Search.string)(self.value)
        target = Search.string.startswith(self.value)

        self.assertEqual(str(test), str(target))

    def test_notstartswith(self):
        test = search.notstartswith(Search.string)(self.value)
        target = not_(Search.string.startswith(self.value))

        self.assertEqual(str(test), str(target))

    def test_endswith(self):
        test = search.endswith(Search.string)(self.value)
        target = Search.string.endswith(self.value)

        self.assertEqual(str(test), str(target))

    def test_notendswith(self):
        test = search.notendswith(Search.string)(self.value)
        target = not_(Search.string.endswith(self.value))

        self.assertEqual(str(test), str(target))

    def test_contains(self):
        test = search.contains(Search.string)(self.value)
        target = Search.string.contains(self.value)

        self.assertEqual(str(test), str(target))

    def test_notcontains(self):
        test = search.notcontains(Search.string)(self.value)
        target = not_(Search.string.contains(self.value))

        self.assertEqual(str(test), str(target))

    def test_icontains(self):
        test = search.icontains(Search.string)(self.value)
        target = Search.string.ilike('%{0}%'.format(self.value))

        self.assertEqual(str(test), str(target))

    def test_noticontains(self):
        test = search.noticontains(Search.string)(self.value)
        target = not_(Search.string.ilike('%{0}%'.format(self.value)))

        self.assertEqual(str(test), str(target))

    def test_in_(self):
        test = search.in_(Search.string)(self.value)
        target = Search.string.in_(self.value)

        self.assertEqual(str(test), str(target))

    def test_notin_(self):
        test = search.notin_(Search.string)(self.value)
        target = not_(Search.string.in_(self.value))

        self.assertEqual(str(test), str(target))

    def test_eq(self):
        test = search.eq(Search.string)(self.value)
        target = Search.string == self.value

        self.assertEqual(str(test), str(target))

    def test_noteq(self):
        test = search.noteq(Search.string)(self.value)
        target = Search.string != self.value

        self.assertEqual(str(test), str(target))

    def test_gt(self):
        test = search.gt(Search.string)(self.value)
        target = Search.string > self.value

        self.assertEqual(str(test), str(target))

    def test_notgt(self):
        test = search.notgt(Search.string)(self.value)
        target = not_(Search.string > self.value)

        self.assertEqual(str(test), str(target))

    def test_ge(self):
        test = search.ge(Search.string)(self.value)
        target = Search.string >= self.value

        self.assertEqual(str(test), str(target))

    def test_notge(self):
        test = search.notge(Search.string)(self.value)
        target = not_(Search.string >= self.value)

        self.assertEqual(str(test), str(target))

    def test_lt(self):
        test = search.lt(Search.string)(self.value)
        target = Search.string < self.value

        self.assertEqual(str(test), str(target))

    def test_notlt(self):
        test = search.notlt(Search.string)(self.value)
        target = not_(Search.string < self.value)

        self.assertEqual(str(test), str(target))

    def test_le(self):
        test = search.le(Search.string)(self.value)
        target = Search.string <= self.value

        self.assertEqual(str(test), str(target))

    def test_notle(self):
        test = search.notle(Search.string)(self.value)
        target = not_(Search.string <= self.value)

        self.assertEqual(str(test), str(target))

    def test_any_(self):
        test = search.any_(
            Search.many, search.eq(SearchMany.string))(self.value)
        target = Search.many.any(SearchMany.string == self.value)

        self.assertEqual(str(test), str(target))

    def test_notany_(self):
        test = search.notany_(
            Search.many, search.eq(SearchMany.string))(self.value)
        target = not_(Search.many.any(SearchMany.string == self.value))

        self.assertEqual(str(test), str(target))

    def test_has(self):
        test = search.has(
            Search.one, search.eq(SearchOne.string))(self.value)
        target = Search.one.has(SearchOne.string == self.value)

        self.assertEqual(str(test), str(target))

    def test_nothas(self):
        test = search.nothas(
            Search.one, search.eq(SearchOne.string))(self.value)
        target = not_(Search.one.has(SearchOne.string == self.value))

        self.assertEqual(str(test), str(target))

    def test_eqenum(self):
        test = search.eqenum(Search.status, OrderStatus)(self.value)
        target = Search.status == OrderStatus.from_string(self.value)

        self.assertEqual(str(test), str(target))

    def test_eqenum_invalid(self):
        test = search.eqenum(Search.status, OrderStatus)('invalid')
        target = None

        self.assertEqual(str(test), str(target))

    def test_noteqenum(self):
        test = search.noteqenum(Search.status, OrderStatus)(self.value)
        target = not_(Search.status == OrderStatus.from_string(self.value))

        self.assertEqual(str(test), str(target))

    def test_noteqenum_invalid(self):
        test = search.noteqenum(Search.status, OrderStatus)('invalid')
        target = not_(None)

        self.assertEqual(str(test), str(target))

    def test_inenum(self):
        test = search.inenum(Search.status, OrderStatus)(self.value)
        target = Search.status.in_([OrderStatus.from_string(self.value)])

        self.assertEqual(str(test), str(target))

    def test_inenum_invalid(self):
        test = search.inenum(Search.status, OrderStatus)('invalid')
        target = None

        self.assertEqual(str(test), str(target))

    def test_notinenum(self):
        test = search.notinenum(Search.status, OrderStatus)(self.value)
        target = not_(Search.status.in_([OrderStatus.from_string(self.value)]))

        self.assertEqual(str(test), str(target))

    def test_notinenum_invalid(self):
        test = search.notinenum(Search.status, OrderStatus)('invalid')
        target = not_(None)

        self.assertEqual(str(test), str(target))

    def test_column_callable(self):
        test = search.like(lambda: Search.string)(self.value)
        target = Search.string.like(self.value)

        self.assertEqual(str(test), str(target))
