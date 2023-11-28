from sqlalchemy import insert, select
from sqlalchemy.sql.functions import func

from db import models
from db.sessions import DBSessionManager
from processor import DbDataModifier
from tests.base import test_engine, AppTestCase
from tests.services import mocks


class TestParseTextFromHtmlService(AppTestCase):
    processor = DbDataModifier

    def setUp(self):
        super().setUp()
        with DBSessionManager(test_engine) as current_session:
            news_content_stmt = insert(models.NewsContent).values(**mocks.TEST_NEWS_CONTENT_ENTITY)
            current_session.execute(news_content_stmt)

    def test_processor(self):
        with DBSessionManager(test_engine) as current_session:
            self.processor().process_db(test_engine)

            assets_count_stmt = select(func.count(models.Assets.asset_id))
            assets_count = current_session.scalar(assets_count_stmt)

            news_assets_count_stmt = select(func.count(models.NewsContentAssets.c.news_content_asset_id))
            news_assets_count = current_session.scalar(news_assets_count_stmt)

            news_content_select_stmt = select(models.NewsContent)
            news_content = current_session.scalar(news_content_select_stmt)

            self.assertNotEqual(news_assets_count, assets_count)
            self.assertEqual(1, news_assets_count)
            self.assertEqual(2, assets_count)
            self.assertTrue(news_content.main_asset_id)
            self.assertTrue(news_content.view_data.get('youtube'))
