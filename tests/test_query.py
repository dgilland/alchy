
from sqlalchemy import orm
import pydash

from alchy import query
from alchy.query import LoadOption
from alchy._compat import iteritems

from .base import TestQueryBase
from .fixtures import Foo, Bar, Baz, Qux


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
        self.assertEqual(
            page_2, self.db.query(Foo).limit(per_page).offset(per_page).all())

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
        self.assertEqual(paginate.pages,
                         int(query.ceil(paginate.total / float(per_page))))

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

    def test_query_paginate_per_page_zero(self):
        query = Foo.query.paginate(per_page=0)
        self.assertEqual(query.per_page, 0)
        self.assertTrue(query.total > 0)

    def test_advanced_search(self):
        search_dict = dict(foo_string='smith', foo_number=3)
        results = Foo.query.search(search_dict=search_dict).all()

        self.assertTrue(len(results) > 0)

        for r in results:
            self.assertTrue(search_dict['foo_string'] in r.string.lower())
            self.assertEqual(search_dict['foo_number'], r.number)

    def test_simple_search(self):
        search_string = 'smith'

        for Model in [Foo, Bar]:
            results = Model.query.search(search_string=search_string).all()

            self.assertTrue(len(results) > 0)

            for r in results:
                self.assertTrue(search_string in r.string.lower())

    def test_search(self):
        search_string = 'smith'
        search_dict = dict(foo_number=3)
        results = Foo.query.search(search_string, search_dict).all()

        self.assertTrue(len(results) > 0)

        for r in results:
            self.assertTrue(search_string in r.string.lower())
            self.assertEqual(search_dict['foo_number'], r.number)

    def test_search_one_to_many(self):
        string_choices = ['one', 'two', 'three']
        string2_choices = ['four', 'five', 'six']

        for i in range(50):
            string = string_choices[i % len(string_choices)]
            string2 = string2_choices[i % len(string_choices)]
            bars = [Bar(string=i) for _ in range(2)]
            self.db.add_commit(Foo(string=string, string2=string2, bars=bars))

        search_string = 'one four'
        limit = 10

        results = Foo.query.join(Foo.bars).search(
            search_string, limit=limit, order_by=Foo.string).all()

        self.assertEqual(len(results), limit)

        search_string = '49'

        results = Foo.query.join(Foo.bars).search(search_string).all()

        self.assertEqual(len(results), 1)

    def test_search_order_by(self):
        ids = Foo.query.search('i').pluck('_id')
        ids_desc = Foo.query.search('i', order_by=Foo._id.desc()).pluck('_id')

        self.assertEqual(ids_desc, list(reversed(ids)))

    def test_search_with_initial_whereclause(self):
        string_choices = ['one', 'two', 'three']
        string2_choices = ['four', 'five', 'six']

        for i in range(50):
            string = string_choices[i % len(string_choices)]
            string2 = string2_choices[i % len(string_choices)]
            bars = [Bar(string=i) for _ in range(2)]
            self.db.add_commit(Foo(string=string, string2=string2, bars=bars))

        search_string = 'one four'
        limit = 7

        qry = Foo.query.join(Foo.bars).filter(Foo._id < 25)
        results = qry.search(
            search_string, limit=limit, order_by=Foo.string).all()

        self.assertEqual(len(results), limit)

    def test_search_empty(self):
        self.assertEqual(str(Foo.query.search()), str(Foo.query))

    def test_search_limit_offset_order_by(self):
        search_string = 'i'
        results1 = (Foo.query
                    .search(search_string,
                            limit=1,
                            offset=1,
                            order_by=Foo.string)
                    .order_by(Foo.string)
                    .all())
        results2 = Foo.query.search(
            search_string).order_by(Foo.string).limit(1).offset(1).all()

        self.assertTrue(len(results1))
        self.assertEqual(results1, results2)

    def test_join_eager(self):
        self.assertEqual(
            str(self.db.query(Foo).join_eager('bars')),
            str((self.db.query(Foo)
                 .join('bars')
                 .options(orm.contains_eager('bars')))),
            'it should join eager on single string entity'
        )

        self.assertEqual(
            str(self.db.query(Foo).join_eager(Foo.bars)),
            str((self.db.query(Foo)
                 .join(Foo.bars)
                 .options(orm.contains_eager(Foo.bars)))),
            'it should join eager on single model entity'
        )

        self.assertEqual(
            str(self.db.query(Foo).join_eager('bars', 'bazs')),
            str((self.db.query(Foo)
                 .join('bars', 'bazs')
                 .options(orm.contains_eager('bars').contains_eager('bazs')))),
            'it should join eager on multiple string entities'
        )

        self.assertEqual(
            str(self.db.query(Foo).join_eager(Foo.bars, Bar.bazs)),
            str(
                self.db.query(Foo).join(Foo.bars, Bar.bazs).options(
                    orm.contains_eager(Foo.bars).contains_eager(Bar.bazs)
                )
            ),
            'it should join eager on multiple model entities'
        )

        self.assertEqual(
            str((self.db.query(Foo)
                 .join_eager('bars',
                             options=[LoadOption('contains_eager', 'bazs')]))),
            str((self.db.query(Foo)
                 .join('bars')
                 .options(orm.contains_eager('bars').contains_eager('bazs')))),
            'it should join eager using options'
        )

    def test_join_eager_with_alias(self):
        bar_alias = orm.aliased(Bar)
        baz_alias = orm.aliased(Baz)

        self.assertEqual(
            str(self.db.query(Foo).join_eager('bars', alias=bar_alias)),
            str((self.db.query(Foo)
                 .join(bar_alias, 'bars')
                 .options(orm.contains_eager('bars', alias=bar_alias)))),
            'it should join eager on alias and string entity'
        )

        self.assertEqual(
            str(self.db.query(Foo).join_eager(Foo.bars, alias=bar_alias)),
            str((self.db.query(Foo)
                 .join(bar_alias, Foo.bars)
                 .options(orm.contains_eager(Foo.bars, alias=bar_alias)))),
            'it should join eager on alias and model entity'
        )

        self.assertEqual(
            str(self.db.query(Foo).join_eager('bars',
                                              'bazs',
                                              alias={'bars': bar_alias,
                                                     'bazs': baz_alias})),
            str((self.db.query(Foo)
                 .join((bar_alias, 'bars'), (baz_alias, 'bazs'))
                 .options((orm.contains_eager('bars', alias=bar_alias)
                           .contains_eager('bazs', alias=baz_alias))))),
            'it should join eager on multiple aliases'
        )

    def test_outerouterjoin_eager(self):
        self.assertEqual(
            str(self.db.query(Foo).outerjoin_eager('bars')),
            str((self.db.query(Foo)
                 .outerjoin('bars')
                 .options(orm.contains_eager('bars')))),
            'it should outerjoin eager on single string entity'
        )

        self.assertEqual(
            str(self.db.query(Foo).outerjoin_eager(Foo.bars)),
            str((self.db.query(Foo)
                 .outerjoin(Foo.bars)
                 .options(orm.contains_eager(Foo.bars)))),
            'it should outerjoin eager on single model entity'
        )

        self.assertEqual(
            str(self.db.query(Foo).outerjoin_eager('bars', 'bazs')),
            str(
                self.db.query(Foo).outerjoin('bars', 'bazs').options(
                    orm.contains_eager('bars').contains_eager('bazs')
                )
            ),
            'it should outerjoin eager on multiple string entities'
        )

        self.assertEqual(
            str(self.db.query(Foo).outerjoin_eager(Foo.bars, Bar.bazs)),
            str(
                self.db.query(Foo).outerjoin(Foo.bars, Bar.bazs).options(
                    orm.contains_eager(Foo.bars).contains_eager(Bar.bazs)
                )
            ),
            'it should outerjoin eager on multiple model entities'
        )

        self.assertEqual(
            str((self.db.query(Foo)
                 .outerjoin_eager(
                     'bars',
                     options=[LoadOption('contains_eager', 'bazs')])
                 )),
            str((self.db.query(Foo)
                 .outerjoin('bars')
                 .options(orm.contains_eager('bars').contains_eager('bazs')))),
            'it should join eager using options'
        )

    def test_outerouterjoin_eager_with_alias(self):
        bar_alias = orm.aliased(Bar)
        baz_alias = orm.aliased(Baz)

        self.assertEqual(
            str(self.db.query(Foo).outerjoin_eager('bars', alias=bar_alias)),
            str((self.db.query(Foo)
                 .outerjoin(bar_alias, 'bars')
                 .options(orm.contains_eager('bars', alias=bar_alias)))),
            'it should outerjoin eager on alias and string entity'
        )

        self.assertEqual(
            str(self.db.query(Foo).outerjoin_eager(Foo.bars, alias=bar_alias)),
            str((self.db.query(Foo)
                 .outerjoin(bar_alias, Foo.bars)
                 .options(orm.contains_eager(Foo.bars, alias=bar_alias)))),
            'it should outerjoin eager on alias and model entity'
        )

        self.assertEqual(
            str(self.db.query(Foo).outerjoin_eager('bars',
                                                   'bazs',
                                                   alias={'bars': bar_alias,
                                                          'bazs': baz_alias})),
            str((self.db.query(Foo)
                 .outerjoin((bar_alias, 'bars'), (baz_alias, 'bazs'))
                 .options((orm.contains_eager('bars', alias=bar_alias)
                           .contains_eager('bazs', alias=baz_alias))))),
            'it should join eager on multiple aliases'
        )

    def test_joinedload(self):
        self.assertEqual(
            str(self.db.query(Foo).joinedload('bars')),
            str(self.db.query(Foo).options(orm.joinedload('bars')))
        )

        self.assertEqual(
            str(self.db.query(Foo).joinedload('bars', 'bazs')),
            str((self.db.query(Foo)
                 .options(orm.joinedload('bars').joinedload('bazs'))))
        )

        self.assertEqual(
            str(self.db.query(Foo).joinedload(Foo.bars)),
            str(self.db.query(Foo).options(orm.joinedload(Foo.bars)))
        )

        self.assertEqual(
            str(self.db.query(Foo).joinedload(Foo.bars, Bar.bazs)),
            str((self.db.query(Foo)
                 .options(orm.joinedload(Foo.bars).joinedload(Bar.bazs))))
        )

        self.assertEqual(
            str((self.db.query(Foo)
                 .joinedload('bars',
                             options=[LoadOption('joinedload', 'bazs')]))),
            str((self.db.query(Foo)
                 .options(orm.joinedload('bars').joinedload('bazs'))))
        )

    def test_immediateload(self):
        self.assertEqual(
            str(self.db.query(Foo).immediateload('bars')),
            str(self.db.query(Foo).options(orm.immediateload('bars')))
        )

        self.assertEqual(
            str(self.db.query(Foo).immediateload('bars', 'bazs')),
            str((self.db.query(Foo)
                 .options(orm.immediateload('bars').immediateload('bazs'))))
        )

        self.assertEqual(
            str(self.db.query(Foo).immediateload(Foo.bars)),
            str(self.db.query(Foo).options(orm.immediateload(Foo.bars)))
        )

        self.assertEqual(
            str(self.db.query(Foo).immediateload(Foo.bars, Bar.bazs)),
            str((self.db.query(Foo)
                .options(orm.immediateload(Foo.bars).immediateload(Bar.bazs))))
        )

        self.assertEqual(
            str((self.db.query(Foo)
                 .immediateload('bars',
                                options=[LoadOption('immediateload',
                                                    'bazs')]))),
            str((self.db.query(Foo)
                 .options(orm.immediateload('bars').immediateload('bazs'))))
        )

    def test_lazyload(self):
        self.assertEqual(
            str(self.db.query(Foo).lazyload('bars')),
            str(self.db.query(Foo).options(orm.lazyload('bars')))
        )

        self.assertEqual(
            str(self.db.query(Foo).lazyload('bars', 'bazs')),
            str((self.db.query(Foo)
                 .options(orm.lazyload('bars').lazyload('bazs'))))
        )

        self.assertEqual(
            str(self.db.query(Foo).lazyload(Foo.bars)),
            str(self.db.query(Foo).options(orm.lazyload(Foo.bars)))
        )

        self.assertEqual(
            str(self.db.query(Foo).lazyload(Foo.bars, Bar.bazs)),
            str((self.db.query(Foo)
                 .options(orm.lazyload(Foo.bars).lazyload(Bar.bazs))))
        )

        self.assertEqual(
            str((self.db.query(Foo)
                 .lazyload('bars', options=[LoadOption('lazyload', 'bazs')]))),
            str((self.db.query(Foo)
                 .options(orm.lazyload('bars').lazyload('bazs'))))
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
            str((self.db.query(Foo)
                 .options(orm.noload(Foo.bars).noload(Bar.bazs))))
        )

        self.assertEqual(
            str((self.db.query(Foo)
                 .noload('bars',
                         options=[LoadOption('noload', 'bazs')]))),
            str(self.db.query(Foo).options(orm.noload('bars').noload('bazs')))
        )

    def test_subqueryload(self):
        self.assertEqual(
            str(self.db.query(Foo).subqueryload('bars')),
            str(self.db.query(Foo).options(orm.subqueryload('bars')))
        )

        self.assertEqual(
            str(self.db.query(Foo).subqueryload('bars', 'bazs')),
            str((self.db.query(Foo)
                 .options(orm.subqueryload('bars').subqueryload('bazs'))))
        )

        self.assertEqual(
            str(self.db.query(Foo).subqueryload(Foo.bars)),
            str(self.db.query(Foo).options(orm.subqueryload(Foo.bars)))
        )

        self.assertEqual(
            str(self.db.query(Foo).subqueryload(Foo.bars, Bar.bazs)),
            str((self.db.query(Foo)
                 .options(orm.subqueryload(Foo.bars).subqueryload(Bar.bazs))))
        )

        self.assertEqual(
            str((self.db.query(Foo)
                 .subqueryload(
                     'bars',
                     options=[LoadOption('subqueryload', 'bazs')]))),
            str((self.db.query(Foo)
                 .options(orm.subqueryload('bars').subqueryload('bazs'))))
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
        item = (self.db.query(Foo)
                .load_only(Foo, '_id', 'string')
                .first().__dict__)
        self.assertIn('string', item)
        self.assertNotIn('number', item)
        self.assertNotIn('boolean', item)

    def test_load_only_using_load_arg(self):
        item = (self.db.query(Foo)
                .load_only(orm.lazyload(Foo.bars), '_id', 'string')
                .first().bars[0].__dict__)
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
        item = (self.db.query(Foo)
                .defer(Foo, 'number', 'boolean')
                .first().__dict__)
        self.assertIn('string', item)
        self.assertNotIn('number', item)
        self.assertNotIn('boolean', item)

    def test_defer_using_load_arg(self):
        item = (self.db.query(Foo)
                .defer(orm.lazyload(Foo.bars), 'number')
                .first().bars[0].__dict__)
        self.assertIn('string', item)
        self.assertNotIn('number', item)

    def test_undefer_with_string_args(self):
        # without undefer()
        item = self.db.query(Foo).first().__dict__
        self.assertNotIn('deferred1_col1', item)
        self.assertNotIn('deferred1_col2', item)

        # with undefer()
        item = (self.db.query(Foo)
                .undefer('deferred1_col1', 'deferred1_col2')
                .first().__dict__)
        self.assertIn('deferred1_col1', item)
        self.assertIn('deferred1_col2', item)

    def test_undefer_using_model_arg(self):
        item = (self.db.query(Foo)
                .undefer(Foo, 'deferred1_col1', 'deferred1_col2')
                .first().__dict__)
        self.assertIn('deferred1_col1', item)
        self.assertIn('deferred1_col2', item)

    def test_undefer_using_load_arg(self):
        item = (self.db.query(Foo)
                .undefer(orm.lazyload(Foo.bars), 'deferred1_col1')
                .first().bars[0].__dict__)
        self.assertIn('deferred1_col1', item)

    def test_undefer_group_with_string_args(self):
        item = self.db.query(Foo).undefer_group('deferred_1').first().__dict__
        self.assertIn('deferred1_col1', item)
        self.assertIn('deferred1_col2', item)
        self.assertNotIn('deferred2_col3', item)
        self.assertNotIn('deferred2_col4', item)

    def test_undefer_group_with_model_arg(self):
        item = (self.db.query(Foo)
                .undefer_group(Foo, 'deferred_1')
                .first().__dict__)
        self.assertIn('deferred1_col1', item)
        self.assertIn('deferred1_col2', item)
        self.assertNotIn('deferred2_col3', item)
        self.assertNotIn('deferred2_col4', item)

    def test_map(self):
        items = self.db.query(Foo).all()
        expected = [i.number * 2 for i in items]

        test = self.db.query(Foo).map(lambda i: i.number * 2)
        self.assertEqual(test, expected)

    def test_reduce(self):
        items = self.db.query(Foo).all()
        expected = sum([i.number for i in items])

        test = (self.db.query(Foo)
                .reduce(lambda result, i: result + i.number, 0))
        self.assertEqual(test, expected)

    def test_reduce_right(self):
        items = self.db.query(Foo).all()

        expected = 1
        for i in reversed(items):
            expected = (i.number * expected) + 1

        def callback(result, item):
            return (item.number * result) + 1

        test = self.db.query(Foo).reduce_right(callback, 1)

        self.assertEqual(test, expected)

    def test_pluck(self):
        expected = sum([i.number for i in self.db.query(Foo).all()])
        test = sum(self.db.query(Foo).pluck('number'))
        self.assertEqual(test, expected)

    def test_index_by(self):
        test = self.db.query(Foo).index_by('_id')
        for _id, item in iteritems(test):
            self.assertEqual(_id, item._id)

    def test_chain(self):
        test = self.db.query(Foo).chain()
        self.assertIsInstance(test, pydash.chaining.Chain)
        self.assertEqual(test.value(), self.db.query(Foo).all())

    def test_model_property(self):
        self.assertIs(Foo.query.Model, Foo)
        self.assertIs(Foo.query.Model, Foo.query.entities[0])
