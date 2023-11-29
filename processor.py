import logging
import math
from datetime import datetime

from sqlalchemy import select, insert, update, delete, not_, create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.sql.functions import count

from db import models
from db.sessions import DBSessionManager
from services.file_uploader import FileUploader
from services.parsers import ParseTextFromHtmlService, ParseAbsoluteToDomesticUrlService


logging.basicConfig()
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)


DEBUG_MODE = False
TEST_DEFAULT_AFFECTED_ROW_COUNT = 2

BATCH_SIZE = 25


class SessionMixin:
    def __init__(self, current_session):
        self.session = current_session


class NewsContentAssetsService(SessionMixin):
    def create_reference_between_news_and_assets(self, news_content_id, asset_id):
        news_content_asset_stmt = insert(models.NewsContentAssets).values(news_content_id=news_content_id,
                                                                          asset_id=asset_id)
        return self.session.execute(news_content_asset_stmt)


class AssetsService(NewsContentAssetsService):
    DEFAULT_USER_ID = 1

    def create_asset(self, file_name):
        asset_insert_stmt = insert(models.Assets).values(file_name=file_name, created_by_id=self.DEFAULT_USER_ID,
                                                         updated_by_id=self.DEFAULT_USER_ID)
        self.session.execute(asset_insert_stmt)

        asset_select_stmt = select(models.Assets).order_by(models.Assets.asset_id.desc())
        return self.session.scalar(asset_select_stmt)

    def create_asset_with_reference(self, news_content_id, file_name):
        asset_insert_stmt = insert(models.Assets).values(file_name=file_name, created_by_id=self.DEFAULT_USER_ID,
                                                         updated_by_id=self.DEFAULT_USER_ID)
        self.session.execute(asset_insert_stmt)

        asset_select_stmt = select(models.Assets).order_by(models.Assets.asset_id.desc())
        asset = self.session.scalar(asset_select_stmt)

        self.create_reference_between_news_and_assets(news_content_id, asset.asset_id)

    def get_asset_by_file_name(self, file_name):
        assets_stmt = select(models.Assets).where(models.Assets.file_name == f'{file_name}')
        return self.session.scalars(assets_stmt).first()


class NewsContentService(SessionMixin):
    def clean_view_data_field(self):
        if DEBUG_MODE:
            return self._DEBUG_clean_view_data_field()

        news_content_stmt = update(models.NewsContent).values(view_data=None).where(
            not_(models.NewsContent.view_data.contains('youtube')))
        self.session.execute(news_content_stmt)

    def _DEBUG_clean_view_data_field(self):
        news_content_select_stmt = select(models.NewsContent.news_content_id).order_by(
            models.NewsContent.news_content_id.desc()).limit(TEST_DEFAULT_AFFECTED_ROW_COUNT)
        news_content_ids = self.session.scalars(news_content_select_stmt).all()

        news_content_stmt = update(models.NewsContent).values(view_data=None).where(
            models.NewsContent.news_content_id.in_(news_content_ids)).where(
            not_(models.NewsContent.view_data.contains('youtube')))
        self.session.execute(news_content_stmt)

    def get_news_contents(self, offset=0):
        if DEBUG_MODE:
            return self._DEBUG_get_news_contents()

        news_content_stmt = select(models.NewsContent).order_by(models.NewsContent.news_content_id.desc()).offset(offset)
        return self.session.scalars(news_content_stmt).all()

    def get_news_contents_from_interval(self, start_id, end_id):
        news_content_stmt = select(models.NewsContent).where(
            models.NewsContent.news_content_id >= start_id,
            models.NewsContent.news_content_id <= end_id
        ).order_by(
            models.NewsContent.news_content_id.desc())
        return self.session.scalars(news_content_stmt).all()

    def _DEBUG_get_news_contents(self):
        news_content_stmt = select(models.NewsContent).order_by(models.NewsContent.news_content_id.desc()).limit(
            TEST_DEFAULT_AFFECTED_ROW_COUNT)
        return self.session.scalars(news_content_stmt).all()

    def get_news_contents_count(self):
        if DEBUG_MODE:
            return self._DEBUG_get_news_contents_count()

        news_content_stmt = select(count(models.NewsContent.news_content_id))
        return self.session.scalar(news_content_stmt)

    def _DEBUG_get_news_contents_count(self):
        return BATCH_SIZE

    def get_news_contents_with_youtube_urls(self):
        if DEBUG_MODE:
            return self._DEBUG_get_news_contents_with_youtube_urls()

        news_content_stmt = select(models.NewsContent).where(models.NewsContent.text.contains('youtube')).order_by(
            models.NewsContent.news_content_id.desc())
        return self.session.scalars(news_content_stmt).all()

    def _DEBUG_get_news_contents_with_youtube_urls(self):
        news_content_stmt = select(models.NewsContent).where(models.NewsContent.text.contains('youtube')).order_by(
            models.NewsContent.news_content_id.desc()).limit(TEST_DEFAULT_AFFECTED_ROW_COUNT)
        return self.session.scalars(news_content_stmt).all()


class DbPreparingService:
    def __init__(self, engine):
        self.engine = engine

    def prepare_db_data(self):
        with DBSessionManager(self.engine) as current_session:
            self._delete_duplicated_news_or_extra_staff(current_session)
            news_service = NewsContentService(current_session)

            for news_content in news_service.get_news_contents():
                news_content = self._extract_main_img_url_into_news_content(news_content, current_session)
            current_session.commit()

            for news_content in news_service.get_news_contents_with_youtube_urls():
                news_content = self._extract_youtube_urls_into_news_content_view_data(news_content)
            current_session.commit()

            news_service.clean_view_data_field()
            news_content.updated_date = datetime.utcnow()
            current_session.commit()

    @staticmethod
    def _delete_duplicated_news_or_extra_staff(current_session):
        news_content_stmt = delete(models.NewsContent).where(models.NewsContent.text == '')
        current_session.execute(news_content_stmt)

    @staticmethod
    def _extract_main_img_url_into_news_content(news_content, current_session):
        absolute_main_image_url = news_content.view_data.get('image_intro', None) if news_content.view_data else None

        if not absolute_main_image_url:
            return news_content

        image_path = ParseAbsoluteToDomesticUrlService().parse_url(absolute_main_image_url)
        file_name = FileUploader.get_file_name_by_path(image_path)

        asset = AssetsService(current_session).get_asset_by_file_name(file_name)
        if asset:
            news_content.main_asset_id = asset.asset_id
        else:
            file_name = FileUploader().upload_file_from_path(image_path)
            if file_name:
                asset = AssetsService(current_session).create_asset(file_name)
                news_content.main_asset_id = asset.asset_id

        return news_content

    @staticmethod
    def _extract_youtube_urls_into_news_content_view_data(news_content):
        parse_service = ParseTextFromHtmlService(news_content.text)
        youtube_urls = parse_service.parse_youtube_urls()

        if not ('youtube' in news_content.view_data):
            news_content.view_data = {}

        news_content.view_data.update({'youtube': youtube_urls})
        return news_content


class DbDataModifier:
    DEFAULT_USER_ID = 1
    TEST_DEFAULT_AFFECTED_ROW_COUNT = 2

    def __init__(self, engine):
        self.engine = engine

    def process_db(self):
        try:
            DbPreparingService(self.engine).prepare_db_data()
            self._modify_db_data()
        except OperationalError as e:
            logging.error(f'Database Error: {e}')

    def modify_db_data_for_entities(self, engine, start_news_content_id, end_news_content_id):
        with DBSessionManager(engine) as current_session:
            news_service = NewsContentService(current_session)
            news_contents = news_service.get_news_contents_from_interval(start_news_content_id, end_news_content_id)
            self._modify_db_data_partial(news_contents, current_session)

            current_session.commit()

    def _modify_db_data(self, ):
        with DBSessionManager(self.engine) as current_session:
            news_service = NewsContentService(current_session)

            total_news_count = news_service.get_news_contents_count()
            iter_times = math.ceil(total_news_count / BATCH_SIZE)

        for _ in range(iter_times):
            with DBSessionManager(self.engine) as current_session:
                news_service = NewsContentService(current_session)
                news_contents = news_service.get_news_contents(BATCH_SIZE)
                self._modify_db_data_partial(news_contents, current_session)

                current_session.commit()

    def _modify_db_data_partial(self, news_contents, current_session):
        for news_content in news_contents:
            parse_service = ParseTextFromHtmlService(news_content.text)
            news_content.text = parse_service.parse_text()

            if not news_content.assets:
                image_urls = parse_service.parse_image_urls()
                self._extract_image_urls_into_assets(news_content, image_urls, current_session)

            news_content.updated_date = datetime.utcnow()
        current_session.commit()

    def _extract_image_urls_into_assets(self, news_content, image_urls, current_session):
        for image_path in image_urls:
            file_name = FileUploader.get_file_name_by_path(image_path)
            asset_service = AssetsService(current_session)
            asset = asset_service.get_asset_by_file_name(file_name)

            current_session.refresh(news_content)

            if asset is None:
                file_name = FileUploader().upload_file_from_path(image_path)
                if file_name:
                    asset_service.create_asset_with_reference(news_content.news_content_id, file_name)

            elif asset and asset not in news_content.assets:
                asset_service.create_reference_between_news_and_assets(
                    news_content.news_content_id, asset.asset_id)
