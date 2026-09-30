"""Database construction without import-time connections or schema mutations."""
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    pass


def create_database_engine(database_url: str) -> Engine:
    url = make_url(database_url)
    options = {"pool_pre_ping": True}
    if url.get_backend_name() == "sqlite":
        options["connect_args"] = {"check_same_thread": False, "timeout": 30}
        if not url.database or url.database == ":memory:":
            options["poolclass"] = StaticPool
        else:
            database_path = Path(url.database).expanduser().resolve()
            database_path.parent.mkdir(parents=True, exist_ok=True)
            url = url.set(database=str(database_path))
    engine = create_engine(url, **options)
    if url.get_backend_name() == "sqlite":
        @event.listens_for(engine, "connect")
        def configure_sqlite(connection, _record):
            cursor = connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA busy_timeout=30000")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.close()
    return engine
