from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from keiba_infrastructure.db import create_database_engine, session_factory
from sqlalchemy.orm import Session

ROOT = Path(__file__).parents[2]


@pytest.fixture
def migrated_session(tmp_path: Path) -> Iterator[Session]:
    database_path = tmp_path / "test.sqlite3"
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{database_path}")
    command.upgrade(config, "head")

    engine = create_database_engine(f"sqlite:///{database_path}")
    session = session_factory(engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()
