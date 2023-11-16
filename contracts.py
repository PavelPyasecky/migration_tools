from sqlalchemy.orm import MappedColumn

from db import models

contracts_map = {
    models.NewsContent.view_data: {

    }
}


class NewsContentViewDataContract:
    contract_model_field: MappedColumn = models.NewsContent.view_data
    contract: dict = {
        'youtube': [
            'https://www.youtube.com/watch?v=VIDEO_ID',
            'https://www.youtube.com/watch?v=VIDEO_ID',
        ],
    }
