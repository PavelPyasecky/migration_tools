from contextlib import contextmanager

from sqlalchemy.orm import Session


@contextmanager
def DBSessionManager(current_engine):
    session = Session(current_engine)
    yield session
    session.commit()
    session.close()
