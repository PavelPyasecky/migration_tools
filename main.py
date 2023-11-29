from db.engine import engine
from processor import DbDataModifier

DbDataModifier(engine).process_db()
