from sqlalchemy import create_engine, select, insert, update
from sqlalchemy.orm import Session

import settings
from db import models
from services.file_uploader import FileUploader
from services.parsers import ParseTextFromHtmlService, ParseAbsoluteToDomesticUrlService

engine = create_engine(settings.DB_CONNECTION_STRING, echo=True)
session = Session(engine)


class DatabaseHandler:
    def __init__(self, current_session):
        self.session = current_session

    def handle(self):
        news_contents = self._get_news_content_list()
        for news_content in news_contents:
            parse_service = ParseTextFromHtmlService(news_content.text)
            self._extract_main_img_url_into_news_content_main_image(news_content, parse_service)
        self.session.commit()

        self._clean_view_data_field()

        for news_content in news_contents:
            parse_service = ParseTextFromHtmlService(news_content.text)

            news_content = self._extract_text_news_content_text(news_content, parse_service)
            self._extract_image_urls_into_assets(news_content, parse_service)
            self._extract_youtube_urls_into_news_content_view_data(news_content, parse_service)
        self.session.commit()

    def _clean_view_data_field(self):
        news_content_stmt = update(models.NewsContent).values(view_data=None)
        self.session.execute(news_content_stmt)

    def _get_news_content_list(self):
        news_content_stmt = select(models.NewsContent).order_by(models.NewsContent.news_content_id.desc()).limit(2)     #TODO remove 'limit()' for production
        return self.session.scalars(news_content_stmt).all()

    def _extract_text_news_content_text(self, news_content, parse_service):
        news_content.text = parse_service.parse_text()
        return news_content

    def _extract_image_urls_into_assets(self, news_content, parse_service):
        image_urls = parse_service.parse_image_urls()
        for image_path in image_urls:
            file_name = self._upload_file_by_file_path(image_path)
            self._create_assets_by_img_url(news_content.news_content_id, file_name)

    @staticmethod
    def _upload_file_by_file_path(file_path):
        file_upload_service = FileUploader()
        file_name = file_upload_service.upload_file_from_path(file_path)
        return file_name

    def _create_assets_by_img_url(self, news_content_id, file_name):
        asset_insert_stmt = insert(models.Assets).values(file_name=file_name)
        self.session.execute(asset_insert_stmt)

        asset_select_stmt = select(models.Assets).order_by(models.Assets.asset_id.desc())
        asset = self.session.scalar(asset_select_stmt).first()

        news_content_asset_stmt = insert(models.NewsContentAssets).values(news_content_id=news_content_id,
                                                                          asset_id=asset.asset_id)
        self.session.execute(news_content_asset_stmt)   #TODO return created instances if posible

    @staticmethod
    def _extract_youtube_urls_into_news_content_view_data(news_content, parse_service):
        youtube_urls = parse_service.parse_youtube_urls()
        new_view_data = news_content.view_data if news_content.view_data else {}
        news_content.view_data = new_view_data['youtube'] = youtube_urls
        return news_content

    def _extract_main_img_url_into_news_content_main_image(self, news_content, parse_service):
        absolute_main_image_url = news_content.view_data.get('image_intro', None) if news_content.view_data else ''
        url_server = ParseAbsoluteToDomesticUrlService()
        image_path = url_server.parse_url(absolute_main_image_url)
        file_name = image_path.split('/')[-1]

        asset = self._get_asset_by_file_name(file_name)
        if asset:
            news_content.main_asset_id = asset.asset_id
        else:
            self._upload_file_by_file_path(image_path)
            self._create_assets_by_img_url(news_content.news_content_id, file_name)
        return news_content

    def _get_asset_by_file_name(self, file_name):
        assets_stmt = select(models.Assets).where(models.Assets.file_name == f'{file_name}')
        return self.session.scalars(assets_stmt).first()


DatabaseHandler(session).handle()
