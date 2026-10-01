from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

ROOT = Path(__file__).parents[2]
EXPECTED_TABLES = {
    "raw_observations",
    "data_snapshots",
    "feature_snapshots",
    "prediction_snapshots",
    "recommendations",
    "results",
    "model_versions",
    "feature_versions",
    "logic_versions",
    "ingestion_batches",
}
REQUIRED_COLUMNS = {
    "feature_snapshots": {"data_snapshot_id", "feature_version_id", "logic_version_id"},
    "prediction_snapshots": {
        "data_snapshot_id",
        "feature_version_id",
        "model_version_id",
        "logic_version_id",
    },
    "recommendations": {
        "data_snapshot_id",
        "prediction_snapshot_id",
        "feature_version_id",
        "model_version_id",
        "logic_version_id",
    },
}


def test_phase_one_migration_round_trips_on_clean_sqlite(tmp_path: Path) -> None:
    database_path = tmp_path / "phase1.sqlite3"
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{database_path}")

    command.upgrade(config, "head")

    engine = create_engine(f"sqlite:///{database_path}")
    inspector = inspect(engine)
    assert EXPECTED_TABLES.issubset(set(inspector.get_table_names()))
    for table_name, columns in REQUIRED_COLUMNS.items():
        actual_columns = {column["name"] for column in inspector.get_columns(table_name)}
        assert columns.issubset(actual_columns)
