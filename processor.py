from sqlalchemy import create_engine

import settings

engine = create_engine(settings.DB_CONNECTION_STRING, echo=True)
