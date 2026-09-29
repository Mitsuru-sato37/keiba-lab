from typing import Any

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Integer,
    MetaData,
    Numeric,
    String,
    Table,
    Text,
    UniqueConstraint,
)

metadata = MetaData()


def lineage_columns() -> tuple[Column[Any], ...]:
    return (
        Column("calculated_at", DateTime(timezone=True), nullable=False),
        Column("snapshot_id", String(128), nullable=False),
        Column("feature_version", String(128), nullable=False),
        Column("model_version", String(128), nullable=False),
        Column("calibration_version", String(128), nullable=False),
        Column("logic_version", String(128), nullable=False),
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

race = Table(
    "race",
    metadata,
    Column("race_id", String(128), primary_key=True),
    Column("provider", String(128), nullable=False),
    Column("scheduled_post_time", DateTime(timezone=True), nullable=False),
    Column("payload", JSON, nullable=False),
)

runner = Table(
    "runner",
    metadata,
    Column("runner_id", String(128), primary_key=True),
    Column("race_id", String(128), nullable=False),
    Column("horse_id", String(128), nullable=False),
    Column("horse_number", Integer, nullable=False),
    Column("payload", JSON, nullable=False),
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

odds_snapshot = Table(
    "odds_snapshot",
    metadata,
    Column("odds_snapshot_id", String(128), primary_key=True),
    Column("race_id", String(128), nullable=False),
    Column("horse_id", String(128), nullable=False),
    Column("observed_at", DateTime(timezone=True), nullable=False),
    Column("current_odds", Numeric(12, 4), nullable=False),
    Column("provider", String(128), nullable=False),
    Column("logic_version", String(128), nullable=False),
)

prediction_snapshot = Table(
    "prediction_snapshot",
    metadata,
    Column("prediction_snapshot_id", String(128), primary_key=True),
    Column("race_id", String(128), nullable=False),
    Column("as_of_time", DateTime(timezone=True), nullable=False),
    *lineage_columns(),
    Column("payload", JSON, nullable=False),
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

logic_version = Table(
    "logic_version",
    metadata,
    Column("logic_version_id", String(128), primary_key=True),
    Column("logic_id", String(128), nullable=False),
    Column("version", String(64), nullable=False),
    Column("manifest", JSON, nullable=False),
)

policy_version = Table(
    "policy_version",
    metadata,
    Column("policy_version_id", String(128), primary_key=True),
    Column("policy_id", String(128), nullable=False),
    Column("version", String(64), nullable=False),
    Column("parameters", JSON, nullable=False),
)
