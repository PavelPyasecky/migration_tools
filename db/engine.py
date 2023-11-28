from sqlalchemy import create_engine

import settings

engine = create_engine(settings.PROD_DB_CONNECTION_STRING, echo=True)
