from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml
from alembic.config import Config
from keiba_infrastructure.schema import Result
from sqlalchemy import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

ROOT = Path(__file__).parents[2]


def test_compose_defines_local_only_postgres_service() -> None:
    compose = yaml.safe_load((ROOT / "docker-compose.yml").read_text(encoding="utf-8"))

    postgres = compose["services"]["postgres"]
    assert postgres["image"].startswith("postgres:")
    assert postgres["ports"] == ["127.0.0.1:5432:5432"]


def test_alembic_environment_contains_the_phase_one_migration() -> None:
    config = Config(str(ROOT / "alembic.ini"))

    assert config.get_main_option("script_location") == "alembic"
    assert (ROOT / "alembic" / "env.py").is_file()
    assert [path.name for path in (ROOT / "alembic" / "versions").glob("*.py")] == [
        "0001_phase1_data_foundation.py",
        "0002_phase2_ingestion_batches.py",
        "0003_phase3_feature_logic_lineage.py",
        "0004_phase5_backtest_records.py",
        "0005_phase6_golden_race.py",
    ]


def test_sqlite_repository_engine_enforces_foreign_keys(migrated_session: Session) -> None:
    with pytest.raises(IntegrityError):
        migrated_session.execute(
            insert(Result).values(
                result_id="result-without-recommendation",
                race_id="race-1",
                recommendation_id="missing-recommendation",
                payload={},
                persisted_at=datetime(2022, 1, 1, tzinfo=UTC),
            ),
        )
