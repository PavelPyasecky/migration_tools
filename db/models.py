from sqlalchemy import String, Integer, Table, ForeignKey
from sqlalchemy.dialects.mysql import MEDIUMTEXT, JSON, DATETIME
from sqlalchemy.orm import Mapped, mapped_column, registry, relationship

mapper_registry = registry()


@mapper_registry.mapped
class NewsContentAssets:
    __tablename__ = "newscontentassets"

    news_content_asset_id = mapped_column(Integer, name='NewsContentAssetId', primary_key=True)
    news_content_id = mapped_column(ForeignKey("newscontent.news_content_id"), name='NewsContentId', primary_key=True)
    asset_id = mapped_column(ForeignKey("assets.asset_id"), name='AssetId', primary_key=True)


@mapper_registry.mapped
class Assets:
    __tablename__ = "assets"

    asset_id = mapped_column(Integer, name='AssetId', primary_key=True)
    file_name = mapped_column(String(500), name='FileName')

    created_date = mapped_column(DATETIME, name='CreatedDate')
    created_by_id = mapped_column(Integer, name='CreatedById')
    updated_date = mapped_column(DATETIME, name='UpdatedDate')
    updated_by_id = mapped_column(Integer, name='UpdatedById')

    news_content = relationship(secondary='newscontentassets', back_populates="assets")

    def __repr__(self) -> str:
        return f"Assets(pk={self.asset_id},file_name={self.file_name})"


@mapper_registry.mapped
class NewsContent:
    __tablename__ = "newscontent"

    news_content_id = mapped_column(Integer, name='NewsContentId', primary_key=True)
    title = mapped_column(String(255), name='Title')
    text = mapped_column(MEDIUMTEXT, name='Text')

    created_date = mapped_column(DATETIME, name='CreatedDate')
    created_by_id = mapped_column(Integer, name='CreatedById')
    updated_date: Mapped[str] = mapped_column(DATETIME, name='UpdatedDate')
    updated_by_id: Mapped[str] = mapped_column(Integer, name='UpdatedById')
    view_data = mapped_column(JSON, name='ViewData')
    main_image = mapped_column(String(100), name='MainImage')

    asset = relationship(secondary='newscontentassets', back_populates="news_contents")

    def __repr__(self) -> str:
        return f"NewsContent(pk={self.news_content_id},title={self.title})"
