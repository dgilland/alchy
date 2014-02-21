
from sqlalchemy import orm

from alchy import query

from .base import TestQueryBase
from fixtures import Foo, Bar, Baz, Qux

class TestQuery(TestQueryBase):

    def test_session_query_class(self):
        """It should be the default class type for Manager session queries"""
        self.assertIsInstance(self.db.query(), query.Query)

    def test_query_entities(self):
        entities = [Foo]
        join_entities = [Bar, Qux, Baz]

        query = self.db.query(*entities).join(*join_entities)

        self.assertEqual(query.entities, entities)
        self.assertEqual(query.join_entities, join_entities)
        self.assertEqual(query.all_entities, entities + join_entities)

    def test_query_page(self):
        per_page = 2

        page_1 = self.db.query(Foo).page(1, per_page).all()
        page_2 = self.db.query(Foo).page(2, per_page).all()

        self.assertTrue(len(page_1) > 0)
        self.assertTrue(len(page_2) > 0)

        self.assertEqual(page_1, self.db.query(Foo).limit(per_page).all())
        self.assertEqual(page_2, self.db.query(Foo).limit(per_page).offset(per_page).all())

    def test_query_page_default_per_page(self):
        query = Foo.query.page(1)
        self.assertEqual(query._limit, Foo.query.DEFAULT_PER_PAGE)

    def test_query_paginate(self):
        per_page = 2

        self.assertRaises(IndexError, self.db.query(Foo).paginate, 0)

        paginate = self.db.query(Foo).paginate(1, per_page)
        page_1 = self.db.query(Foo).limit(per_page).all()
        page_2 = self.db.query(Foo).limit(per_page).offset(per_page).all()

        self.assertEqual(paginate.items, page_1)
        self.assertEqual(paginate.prev_num, 0)
        self.assertFalse(paginate.has_prev)
        self.assertEqual(paginate.page, 1)
        self.assertEqual(paginate.next_num, 2)
        self.assertTrue(paginate.has_next)
        self.assertEqual(paginate.per_page, per_page)
        self.assertEqual(paginate.total, self.db.query(Foo).count())
        self.assertEqual(paginate.pages, int(query.ceil(paginate.total / float(per_page))))

        next_page = paginate.next()

        self.assertEqual(next_page.items, page_2)
        self.assertEqual(next_page.prev_num, 1)
        self.assertTrue(next_page.has_prev)
        self.assertEqual(next_page.page, 2)
        self.assertEqual(next_page.next_num, 3)
        self.assertTrue(next_page.has_next)

        next_next_page = next_page.next()
        self.assertFalse(next_next_page.has_next)

        self.assertRaises(IndexError, next_next_page.next, error_out=True)

        prev_page = paginate.prev()

        self.assertEqual(prev_page.items, page_1)

    def test_query_paginate_default_per_page(self):
        query = Foo.query.paginate(1)
        self.assertEqual(query.per_page, Foo.query.DEFAULT_PER_PAGE)

    def test_advanced_search(self):
        search_dict = dict(foo_string='smith', foo_number=3)
        results = self.db.query(Foo).advanced_search(search_dict).all()

        self.assertTrue(len(results) > 0)

        for r in results:
            self.assertTrue(search_dict['foo_string'] in r.string.lower())
            self.assertEqual(search_dict['foo_number'], r.number)

    def test_simple_search(self):
        search_string = 'smith'
        results = self.db.query(Foo).simple_search(search_string).all()

        self.assertTrue(len(results) > 0)

        for r in results:
            self.assertTrue(search_string in r.string.lower())

    def test_search(self):
        search_string = 'smith'
        search_dict = dict(foo_number=3)
        results = self.db.query(Foo).search(search_string, search_dict).all()

        self.assertTrue(len(results) > 0)

        for r in results:
            self.assertTrue(search_string in r.string.lower())
            self.assertEqual(search_dict['foo_number'], r.number)

    def test_search_limit_offset(self):
        search_string = 'i'
        results1 = self.db.query(Foo).search(search_string, limit=1, offset=1).all()
        results2 = self.db.query(Foo).search(search_string).limit(1).offset(1).all()

        self.assertTrue(len(results1))
        self.assertEqual(results1, results2)

    def test_search_joined(self):
        foo = Foo(string='my foo string', number=7, bars=[Bar(string='my bar string', number=1)])
        self.db.add(foo)

        search_string = 'my bar'
        search_dict = dict(foo_number=7)
        results = self.db.query(Foo).join(Bar).search(search_string, search_dict).all()

        self.assertTrue(len(results) == 1)
        self.assertEqual(foo, results[0])

    def test_join_eager(self):
        self.assertEqual(
            str(self.db.query(Foo).join_eager('bars')),
            str(self.db.query(Foo).join('bars').options(orm.contains_eager('bars'))),
            'it should join eager on single string entity'
        )

        self.assertEqual(
            str(self.db.query(Foo).join_eager(Foo.bars)),
            str(self.db.query(Foo).join(Foo.bars).options(orm.contains_eager(Foo.bars))),
            'it should join eager on single model entity'
        )

        self.assertEqual(
            str(self.db.query(Foo).join_eager('bars', 'bazs')),
            str(self.db.query(Foo).join('bars', 'bazs').options(orm.contains_eager('bars').contains_eager('bazs'))),
            'it should join eager on multiple string entities'
        )

        self.assertEqual(
            str(self.db.query(Foo).join_eager(Foo.bars, Bar.bazs)),
            str(self.db.query(Foo).join(Foo.bars, Bar.bazs).options(orm.contains_eager(Foo.bars).contains_eager(Bar.bazs))),
            'it should join eager on multiple model entities'
        )

    def test_join_eager_with_alias(self):
        bar_alias = orm.aliased(Bar)

        self.assertEqual(
            str(self.db.query(Foo).join_eager('bars', alias=bar_alias)),
            str(self.db.query(Foo).join(bar_alias, 'bars').options(orm.contains_eager('bars', alias=bar_alias))),
            'it should join eager on alias and string entity'
        )

        self.assertEqual(
            str(self.db.query(Foo).join_eager(Foo.bars, alias=bar_alias)),
            str(self.db.query(Foo).join(bar_alias, Foo.bars).options(orm.contains_eager(Foo.bars, alias=bar_alias))),
            'it should join eager on alias and model entity'
        )

    def test_outerouterjoin_eager(self):
        self.assertEqual(
            str(self.db.query(Foo).outerjoin_eager('bars')),
            str(self.db.query(Foo).outerjoin('bars').options(orm.contains_eager('bars'))),
            'it should outerjoin eager on single string entity'
        )

        self.assertEqual(
            str(self.db.query(Foo).outerjoin_eager(Foo.bars)),
            str(self.db.query(Foo).outerjoin(Foo.bars).options(orm.contains_eager(Foo.bars))),
            'it should outerjoin eager on single model entity'
        )

        self.assertEqual(
            str(self.db.query(Foo).outerjoin_eager('bars', 'bazs')),
            str(self.db.query(Foo).outerjoin('bars', 'bazs').options(orm.contains_eager('bars').contains_eager('bazs'))),
            'it should outerjoin eager on multiple string entities'
        )

        self.assertEqual(
            str(self.db.query(Foo).outerjoin_eager(Foo.bars, Bar.bazs)),
            str(self.db.query(Foo).outerjoin(Foo.bars, Bar.bazs).options(orm.contains_eager(Foo.bars).contains_eager(Bar.bazs))),
            'it should outerjoin eager on multiple model entities'
        )

    def test_outerouterjoin_eager_with_alias(self):
        bar_alias = orm.aliased(Bar)

        self.assertEqual(
            str(self.db.query(Foo).outerjoin_eager('bars', alias=bar_alias)),
            str(self.db.query(Foo).outerjoin(bar_alias, 'bars').options(orm.contains_eager('bars', alias=bar_alias))),
            'it should outerjoin eager on alias and string entity'
        )

        self.assertEqual(
            str(self.db.query(Foo).outerjoin_eager(Foo.bars, alias=bar_alias)),
            str(self.db.query(Foo).outerjoin(bar_alias, Foo.bars).options(orm.contains_eager(Foo.bars, alias=bar_alias))),
            'it should outerjoin eager on alias and model entity'
        )

    def test_joinedload(self):
        self.assertEqual(
            str(self.db.query(Foo).joinedload('bars')),
            str(self.db.query(Foo).options(orm.joinedload('bars')))
        )

        self.assertEqual(
            str(self.db.query(Foo).joinedload('bars', 'bazs')),
            str(self.db.query(Foo).options(orm.joinedload('bars').joinedload('bazs')))
        )

        self.assertEqual(
            str(self.db.query(Foo).joinedload(Foo.bars)),
            str(self.db.query(Foo).options(orm.joinedload(Foo.bars)))
        )

        self.assertEqual(
            str(self.db.query(Foo).joinedload(Foo.bars, Bar.bazs)),
            str(self.db.query(Foo).options(orm.joinedload(Foo.bars).joinedload(Bar.bazs)))
        )

    def test_immediateload(self):
        self.assertEqual(
            str(self.db.query(Foo).immediateload('bars')),
            str(self.db.query(Foo).options(orm.immediateload('bars')))
        )

        self.assertEqual(
            str(self.db.query(Foo).immediateload('bars', 'bazs')),
            str(self.db.query(Foo).options(orm.immediateload('bars').immediateload('bazs')))
        )

        self.assertEqual(
            str(self.db.query(Foo).immediateload(Foo.bars)),
            str(self.db.query(Foo).options(orm.immediateload(Foo.bars)))
        )

        self.assertEqual(
            str(self.db.query(Foo).immediateload(Foo.bars, Bar.bazs)),
            str(self.db.query(Foo).options(orm.immediateload(Foo.bars).immediateload(Bar.bazs)))
        )

    def test_lazyload(self):
        self.assertEqual(
            str(self.db.query(Foo).lazyload('bars')),
            str(self.db.query(Foo).options(orm.lazyload('bars')))
        )

        self.assertEqual(
            str(self.db.query(Foo).lazyload('bars', 'bazs')),
            str(self.db.query(Foo).options(orm.lazyload('bars').lazyload('bazs')))
        )

        self.assertEqual(
            str(self.db.query(Foo).lazyload(Foo.bars)),
            str(self.db.query(Foo).options(orm.lazyload(Foo.bars)))
        )

        self.assertEqual(
            str(self.db.query(Foo).lazyload(Foo.bars, Bar.bazs)),
            str(self.db.query(Foo).options(orm.lazyload(Foo.bars).lazyload(Bar.bazs)))
        )

    def test_noload(self):
        self.assertEqual(
            str(self.db.query(Foo).noload('bars')),
            str(self.db.query(Foo).options(orm.noload('bars')))
        )

        self.assertEqual(
            str(self.db.query(Foo).noload('bars', 'bazs')),
            str(self.db.query(Foo).options(orm.noload('bars').noload('bazs')))
        )

        self.assertEqual(
            str(self.db.query(Foo).noload(Foo.bars)),
            str(self.db.query(Foo).options(orm.noload(Foo.bars)))
        )

        self.assertEqual(
            str(self.db.query(Foo).noload(Foo.bars, Bar.bazs)),
            str(self.db.query(Foo).options(orm.noload(Foo.bars).noload(Bar.bazs)))
        )

    def test_subqueryload(self):
        self.assertEqual(
            str(self.db.query(Foo).subqueryload('bars')),
            str(self.db.query(Foo).options(orm.subqueryload('bars')))
        )

        self.assertEqual(
            str(self.db.query(Foo).subqueryload('bars', 'bazs')),
            str(self.db.query(Foo).options(orm.subqueryload('bars').subqueryload('bazs')))
        )

        self.assertEqual(
            str(self.db.query(Foo).subqueryload(Foo.bars)),
            str(self.db.query(Foo).options(orm.subqueryload(Foo.bars)))
        )

        self.assertEqual(
            str(self.db.query(Foo).subqueryload(Foo.bars, Bar.bazs)),
            str(self.db.query(Foo).options(orm.subqueryload(Foo.bars).subqueryload(Bar.bazs)))
        )

    def test_load_only_with_string_args(self):
        # with load_only()
        item = self.db.query(Foo).load_only('_id', 'string').first().__dict__
        self.assertIn('string', item)
        self.assertNotIn('number', item)
        self.assertNotIn('boolean', item)

        # without load_only()
        item = self.db.query(Foo).first().__dict__
        self.assertIn('string', item)
        self.assertIn('number', item)
        self.assertIn('boolean', item)

    def test_load_only_using_model_arg(self):
        item = self.db.query(Foo).load_only(Foo, '_id', 'string').first().__dict__
        self.assertIn('string', item)
        self.assertNotIn('number', item)
        self.assertNotIn('boolean', item)

    def test_defer_with_string_args(self):
        # with defer()
        item = self.db.query(Foo).defer('number', 'boolean').first().__dict__
        self.assertIn('string', item)
        self.assertNotIn('number', item)
        self.assertNotIn('boolean', item)

        # without defer()
        item = self.db.query(Foo).first().__dict__
        self.assertIn('string', item)
        self.assertIn('number', item)
        self.assertIn('boolean', item)

    def test_defer_using_model_arg(self):
        item = self.db.query(Foo).defer(Foo, 'number', 'boolean').first().__dict__
        self.assertIn('string', item)
        self.assertNotIn('number', item)
        self.assertNotIn('boolean', item)

    def test_undefer_with_string_args(self):
        # without undefer()
        item = self.db.query(Foo).first().__dict__
        self.assertNotIn('deferred1_col1', item)
        self.assertNotIn('deferred1_col2', item)

        # with undefer()
        item = self.db.query(Foo).undefer('deferred1_col1', 'deferred1_col2').first().__dict__
        self.assertIn('deferred1_col1', item)
        self.assertIn('deferred1_col2', item)

    def test_undefer_using_model_arg(self):
        item = self.db.query(Foo).undefer(Foo, 'deferred1_col1', 'deferred1_col2').first().__dict__
        self.assertIn('deferred1_col1', item)
        self.assertIn('deferred1_col2', item)

    def test_undefer_group_with_string_args(self):
        item = self.db.query(Foo).undefer_group('deferred_1').first().__dict__
        self.assertIn('deferred1_col1', item)
        self.assertIn('deferred1_col2', item)
        self.assertNotIn('deferred2_col3', item)
        self.assertNotIn('deferred2_col4', item)

    def test_undefer_group_with_model_arg(self):
        item = self.db.query(Foo).undefer_group(Foo, 'deferred_1').first().__dict__
        self.assertIn('deferred1_col1', item)
        self.assertIn('deferred1_col2', item)
        self.assertNotIn('deferred2_col3', item)
        self.assertNotIn('deferred2_col4', item)

    def test_map(self):
        items = self.db.query(Foo).all()
        expected = [i.number*2 for i in items]

        test = self.db.query(Foo).map(lambda i: i.number*2)
        self.assertEqual(test, expected)

    def test_reduce(self):
        items = self.db.query(Foo).all()
        expected = sum([i.number for i in items])

        test = self.db.query(Foo).reduce(lambda result, i: result + i.number, 0)
        self.assertEqual(test, expected)

    def test_reduce_right(self):
        items = self.db.query(Foo).all()
        expected = 1
        for i in reversed(items):
            expected = (i.number * expected) + 1

        test = self.db.query(Foo).reduce_right(lambda result, i: (i.number * result) + 1, 1)
        self.assertEqual(test, expected)

    def test_pluck(self):
        expected = sum([i.number for i in self.db.query(Foo).all()])
        test = sum(self.db.query(Foo).pluck('number'))

        self.assertEqual(test, expected)

