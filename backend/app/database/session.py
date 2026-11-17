"""SQLAlchemy engine/session setup; SQLite is the local MVP default."""

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    pass


connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def migrate_local_schema() -> None:
    """Additive SQLite migration; legacy invoice rows stay ownerless."""
    if not settings.database_url.startswith("sqlite"):
        return
    inspector = inspect(engine)
    if "invoices" in inspector.get_table_names():
        columns = {column["name"] for column in inspector.get_columns("invoices")}
        if "user_id" not in columns:
            with engine.begin() as connection:
                connection.execute(text("ALTER TABLE invoices ADD COLUMN user_id VARCHAR(36) NULL"))
                connection.execute(text("CREATE INDEX IF NOT EXISTS ix_invoices_user_id ON invoices (user_id)"))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
