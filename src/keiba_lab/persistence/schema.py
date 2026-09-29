from typing import Any

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
)

metadata = MetaData()


def lineage_columns() -> tuple[Column[Any], ...]:
    return (
        Column("calculated_at", DateTime(timezone=True)),
        Column("snapshot_id", String(128)),
        Column("feature_version", String(128)),
        Column("model_version", String(128)),
        Column("calibration_version", String(128)),
        Column("logic_version", String(128)),
    )


raw_observation = Table(
    "raw_observation",
    metadata,
    Column("observation_id", String(128), primary_key=True),
    Column("provider", String(128), nullable=False),
    Column("provider_key", String(256), nullable=False),
    Column("source_timestamp", DateTime(timezone=True)),
    Column("received_timestamp", DateTime(timezone=True), nullable=False),
    Column("effective_from", DateTime(timezone=True), nullable=False),
    Column("effective_to", DateTime(timezone=True)),
    Column("snapshot_id", String(128), nullable=False),
    Column("ingestion_batch_id", String(128), nullable=False),
    Column("batch_status", String(64), nullable=False),
    Column("content_checksum", String(128), nullable=False),
    Column("payload", JSON, nullable=False),
    UniqueConstraint("provider", "provider_key", "effective_from", name="uq_raw_provider_version"),
)

race_snapshot = Table(
    "race_snapshot",
    metadata,
    Column("snapshot_id", String(128), primary_key=True),
    Column("race_id", String(128), nullable=False),
    Column("as_of_time", DateTime(timezone=True), nullable=False),
    Column("data_snapshot_id", String(128), nullable=False),
    Column("feature_version", String(128), nullable=False),
    Column("logic_version", String(128), nullable=False),
    Column("membership", JSON, nullable=False),
)

horse_prediction = Table(
    "horse_prediction",
    metadata,
    Column("prediction_id", String(128), primary_key=True),
    Column("race_id", String(128), nullable=False),
    Column("horse_id", String(128), nullable=False),
    *lineage_columns(),
    Column("payload", JSON, nullable=False),
)

recommendation = Table(
    "recommendation",
    metadata,
    Column("recommendation_id", String(128), primary_key=True),
    Column("race_id", String(128), nullable=False),
    Column("prediction_snapshot_id", String(128), nullable=False),
    Column("decision", String(32), nullable=False),
    *lineage_columns(),
    Column("payload", JSON, nullable=False),
)

backtest_run = Table(
    "backtest_run",
    metadata,
    Column("run_id", String(128), primary_key=True),
    Column("status", String(32), nullable=False),
    Column("first_test_year", Integer, nullable=False),
    Column("logic_version", String(128), nullable=False),
    Column("invalid_reason", Text),
    Column("manifest", JSON, nullable=False),
)
