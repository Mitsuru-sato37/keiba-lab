from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


def test_initial_migration_round_trips_on_clean_sqlite_database(tmp_path: Path) -> None:
    database_path = tmp_path / "phase1.db"
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", f"sqlite:///{database_path}")
    command.upgrade(config, "head")
    tables = set(inspect(create_engine(f"sqlite:///{database_path}")).get_table_names())
    assert {
        "alembic_version",
        "race",
        "odds_snapshot",
        "prediction_snapshot",
        "recommendation",
    } <= tables
