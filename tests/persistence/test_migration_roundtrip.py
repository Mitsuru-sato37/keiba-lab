from pathlib import Path

from alembic.config import Config
from sqlalchemy import create_engine, inspect

from alembic import command


def test_initial_migration_round_trips_on_clean_sqlite_database() -> None:
    database_path = Path(".phase1-roundtrip.db")
    engine = None
    try:
        config = Config("alembic.ini")
        config.set_main_option("sqlalchemy.url", f"sqlite:///{database_path.resolve()}")
        command.upgrade(config, "head")
        engine = create_engine(f"sqlite:///{database_path.resolve()}")
        tables = set(inspect(engine).get_table_names())
        assert {
            "alembic_version",
            "race",
            "odds_snapshot",
            "prediction_snapshot",
            "recommendation",
        } <= tables
    finally:
        if engine is not None:
            engine.dispose()
        database_path.unlink(missing_ok=True)
