from datetime import datetime

from sqlalchemy import create_engine, select, insert, update, delete
from sqlalchemy.orm import Session

import settings
from db import models
from services.file_uploader import FileUploader
from services.parsers import ParseTextFromHtmlService, ParseAbsoluteToDomesticUrlService


engine = create_engine(settings.DB_CONNECTION_STRING, echo=True)
session = Session(engine)

DEBUG_MODE = True
TEST_DEFAULT_AFFECTED_ROW_COUNT = 2


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

    def create_asset(self, news_content_id, file_name):
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

        news_content_stmt = update(models.NewsContent).values(view_data=None)
        self.session.execute(news_content_stmt)

    def _DEBUG_clean_view_data_field(self):
        news_content_select_stmt = select(models.NewsContent.news_content_id).order_by(
            models.NewsContent.news_content_id.desc()).limit(TEST_DEFAULT_AFFECTED_ROW_COUNT)
        news_content_ids = self.session.scalars(news_content_select_stmt).all()

        news_content_stmt = update(models.NewsContent).values(view_data=None).where(
            models.NewsContent.news_content_id.in_(news_content_ids))
        self.session.execute(news_content_stmt)

    def get_news_contents(self):
        if DEBUG_MODE:
            return self._DEBUG_get_news_contents()

        news_content_stmt = select(models.NewsContent).order_by(models.NewsContent.news_content_id.desc())
        return self.session.scalars(news_content_stmt).all()

    def _DEBUG_get_news_contents(self):
        news_content_stmt = select(models.NewsContent).order_by(models.NewsContent.news_content_id.desc()).limit(
            TEST_DEFAULT_AFFECTED_ROW_COUNT)
        return self.session.scalars(news_content_stmt).all()


class DbPreparingService(SessionMixin):
    def prepare_db_data(self):
        self._delete_duplicated_news_or_extra_staff()
        news_service = NewsContentService(self.session)

        for news_content in news_service.get_news_contents():
            self._extract_main_img_url_into_news_content(news_content)
        self.session.commit()

        news_service.clean_view_data_field()

    def _delete_duplicated_news_or_extra_staff(self):
        news_content_stmt = delete(models.NewsContent).where(models.NewsContent.text == '')
        self.session.execute(news_content_stmt)

    def _extract_main_img_url_into_news_content(self, news_content):
        absolute_main_image_url = news_content.view_data.get('image_intro', None) if news_content.view_data else None

        if not absolute_main_image_url:
            return news_content

        image_path = ParseAbsoluteToDomesticUrlService().parse_url(absolute_main_image_url)
        file_name = image_path.split('/')[-1]

        asset = AssetsService(self.session).get_asset_by_file_name(file_name)
        if asset:
            news_content.main_asset_id = asset.asset_id
            news_content.updated_date = datetime.utcnow()
        else:
            FileUploader().upload_file_from_path(image_path)
            AssetsService(self.session).create_asset(news_content.news_content_id, file_name)

        return news_content


class DbDataModifier(SessionMixin):
    DEFAULT_USER_ID = 1
    TEST_DEFAULT_AFFECTED_ROW_COUNT = 2

    def process_db(self):
        DbPreparingService(self.session).prepare_db_data()
        self._modify_db_data()

    def _modify_db_data(self):
        for news_content in NewsContentService(self.session).get_news_contents():
            parse_service = ParseTextFromHtmlService(news_content.text)
            news_content.text = parse_service.parse_text()

            if not news_content.assets:
                image_urls = parse_service.parse_image_urls()
                self._extract_image_urls_into_assets(news_content, image_urls)

                youtube_urls = parse_service.parse_youtube_urls()
                news_content = self._extract_youtube_urls_into_news_content_view_data(news_content, youtube_urls)

            news_content.updated_date = datetime.utcnow()
        self.session.commit()

    def _extract_image_urls_into_assets(self, news_content, image_urls):
        for image_path in image_urls:
            file_name = image_path.split('/')[-1]
            asset_service = AssetsService(self.session)
            asset = asset_service.get_asset_by_file_name(file_name)

            if asset:
                asset_service.create_reference_between_news_and_assets(
                    news_content.news_content_id, asset.asset_id)
            else:
                file_name = FileUploader().upload_file_from_path(image_path)
                asset_service.create_asset(news_content.news_content_id, file_name)

    @staticmethod
    def _extract_youtube_urls_into_news_content_view_data(news_content, youtube_urls):
        if not news_content.view_data:
            news_content.view_data = {}

        news_content.view_data.update({'youtube': youtube_urls})
        return news_content


DbDataModifier(session).process_db()
