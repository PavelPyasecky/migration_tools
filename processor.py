from sqlalchemy import create_engine, select, insert
from sqlalchemy.orm import Session

import settings
from db import models
from services.file_uploader import FileUploader
from services.parsers import ParseTextFromHtmlService


engine = create_engine(settings.DB_CONNECTION_STRING, echo=True)
session = Session(engine)


class DatabaseHandler:
    def __init__(self, current_session):
        self.session = current_session

    def handle(self):

        news_contents = self._get_news_content()
        for news_content in news_contents:
            parser_service = ParseTextFromHtmlService(news_content.text)

            news_content.text = parser_service.parse_text()
            img_urls = parser_service.parse_image_urls()

            for img_path in img_urls:
                file_upload_service = FileUploader()
                file_name = file_upload_service.upload_file_from_path(img_path)
                self._create_assets_by_img_url(news_content.news_content_id, file_name)

            # TODO add saving youtube_url to the view_data

    def _get_news_content(self):
        news_content_stmt = select(models.NewsContent).one()    #TODO remove one()
        return self.session.scalars(news_content_stmt)

    def _create_assets_by_img_url(self, news_content_id, file_name):
        asset_stmt = insert(models.Assets).values(news_content_id=news_content_id, file_name=file_name).returning(
            models.Assets.asset_id)
        asset_id = self.session.execute(asset_stmt)

        news_content_asset_stmt = insert(models.NewsContentAssets).values(news_content_id=news_content_id, asset_id=asset_id)
        self.session.execute(news_content_asset_stmt)
