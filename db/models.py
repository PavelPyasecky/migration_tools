from datetime import datetime

from sqlalchemy import String, Integer, ForeignKey, DateTime, Table, Column
from sqlalchemy.dialects.mysql import MEDIUMTEXT, JSON
from sqlalchemy.orm import mapped_column, registry, relationship, DeclarativeBase


class Base(DeclarativeBase):
    pass


mapper_registry = registry(metadata=Base.metadata)


NewsContentAssets = Table(
    "news_content_assets",
    Base.metadata,
    Column("news_content_asset_id", Integer, primary_key=True),
    Column("news_content_id", ForeignKey('news_content.news_content_id')),
    Column("asset_id", ForeignKey('assets.asset_id')),
)


@mapper_registry.mapped
class Assets:
    __tablename__ = 'assets'

    asset_id = mapped_column(Integer, primary_key=True)
    file_name = mapped_column(String(500))

    created_date = mapped_column(DateTime, default=datetime.utcnow)
    created_by_id = mapped_column(Integer)
    updated_date = mapped_column(DateTime, default=datetime.utcnow)
    updated_by_id = mapped_column(Integer)

    def __repr__(self) -> str:
        return f'Assets(pk={self.asset_id},file_name={self.file_name})'


@mapper_registry.mapped
class NewsContent:
    __tablename__ = 'news_content'

    news_content_id = mapped_column(Integer, primary_key=True)
    title = mapped_column(String(255))
    text = mapped_column(MEDIUMTEXT)

    created_date = mapped_column(DateTime, default=datetime.utcnow)
    created_by_id = mapped_column(Integer)
    updated_date = mapped_column(DateTime, default=datetime.utcnow)
    updated_by_id = mapped_column(Integer)
    view_data = mapped_column(JSON)
    main_asset_id = mapped_column(ForeignKey('assets.asset_id'), nullable=True)
    main_asset = relationship('Assets')

    assets = relationship(Assets, secondary=NewsContentAssets,
                          primaryjoin=(NewsContentAssets.c.news_content_id == news_content_id),
                          secondaryjoin=(NewsContentAssets.c.asset_id == Assets.asset_id))

    def __repr__(self) -> str:
        return f'NewsContent(pk={self.news_content_id},title={self.title})'
