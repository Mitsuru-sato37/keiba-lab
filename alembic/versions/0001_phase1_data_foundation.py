"""Create the Phase 1 point-in-time data foundation."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision = "0001_phase1_data_foundation"
down_revision = None
branch_labels = None
depends_on = None

IMMUTABLE_TABLES: Sequence[str] = (
    "raw_observations",
    "data_snapshots",
    "feature_snapshots",
    "prediction_snapshots",
    "recommendations",
    "results",
)


def upgrade() -> None:
    op.create_table(
        "model_versions",
        sa.Column("version_id", sa.String(128), primary_key=True),
        sa.Column("model_name", sa.String(128), nullable=False),
        sa.Column("manifest", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "feature_versions",
        sa.Column("version_id", sa.String(128), primary_key=True),
        sa.Column("feature_name", sa.String(128), nullable=False),
        sa.Column("manifest", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "logic_versions",
        sa.Column("version_id", sa.String(128), primary_key=True),
        sa.Column("logic_id", sa.String(128), nullable=False),
        sa.Column("manifest", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "raw_observations",
        sa.Column("observation_id", sa.String(128), primary_key=True),
        sa.Column("provider", sa.String(128), nullable=False),
        sa.Column("provider_version", sa.String(128), nullable=False),
        sa.Column("provider_record_type", sa.String(128), nullable=False),
        sa.Column("provider_record_key", sa.String(256), nullable=False),
        sa.Column("source_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("received_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("effective_to", sa.DateTime(timezone=True)),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("payload_checksum", sa.String(128), nullable=False),
        sa.Column("ingestion_batch_id", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_raw_observations_temporal",
        "raw_observations",
        ["received_timestamp", "effective_from", "effective_to"],
    )
    op.create_table(
        "data_snapshots",
        sa.Column("snapshot_id", sa.String(128), primary_key=True),
        sa.Column("as_of_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("data_version", sa.String(128), nullable=False),
        sa.Column("manifest", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "feature_snapshots",
        sa.Column("feature_snapshot_id", sa.String(128), primary_key=True),
        sa.Column("race_id", sa.String(128), nullable=False),
        sa.Column("horse_id", sa.String(128), nullable=False),
        sa.Column("as_of_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "data_snapshot_id",
            sa.String(128),
            sa.ForeignKey("data_snapshots.snapshot_id"),
            nullable=False,
        ),
        sa.Column(
            "feature_version_id",
            sa.String(128),
            sa.ForeignKey("feature_versions.version_id"),
            nullable=False,
        ),
        sa.Column("values", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "prediction_snapshots",
        sa.Column("prediction_snapshot_id", sa.String(128), primary_key=True),
        sa.Column("race_id", sa.String(128), nullable=False),
        sa.Column("as_of_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "data_snapshot_id",
            sa.String(128),
            sa.ForeignKey("data_snapshots.snapshot_id"),
            nullable=False,
        ),
        sa.Column(
            "feature_version_id",
            sa.String(128),
            sa.ForeignKey("feature_versions.version_id"),
            nullable=False,
        ),
        sa.Column(
            "model_version_id",
            sa.String(128),
            sa.ForeignKey("model_versions.version_id"),
            nullable=False,
        ),
        sa.Column(
            "logic_version_id",
            sa.String(128),
            sa.ForeignKey("logic_versions.version_id"),
            nullable=False,
        ),
        sa.Column("predictions", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "recommendations",
        sa.Column("recommendation_id", sa.String(128), primary_key=True),
        sa.Column("race_id", sa.String(128), nullable=False),
        sa.Column("decision", sa.String(8), nullable=False),
        sa.Column("strategy", sa.String(64), nullable=False),
        sa.Column(
            "data_snapshot_id",
            sa.String(128),
            sa.ForeignKey("data_snapshots.snapshot_id"),
            nullable=False,
        ),
        sa.Column(
            "prediction_snapshot_id",
            sa.String(128),
            sa.ForeignKey("prediction_snapshots.prediction_snapshot_id"),
            nullable=False,
        ),
        sa.Column(
            "feature_version_id",
            sa.String(128),
            sa.ForeignKey("feature_versions.version_id"),
            nullable=False,
        ),
        sa.Column(
            "model_version_id",
            sa.String(128),
            sa.ForeignKey("model_versions.version_id"),
            nullable=False,
        ),
        sa.Column(
            "logic_version_id",
            sa.String(128),
            sa.ForeignKey("logic_versions.version_id"),
            nullable=False,
        ),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("persisted_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("decision IN ('BUY', 'SKIP')", name="ck_recommendation_decision"),
    )
    op.create_table(
        "results",
        sa.Column("result_id", sa.String(128), primary_key=True),
        sa.Column("race_id", sa.String(128), nullable=False),
        sa.Column(
            "recommendation_id",
            sa.String(128),
            sa.ForeignKey("recommendations.recommendation_id"),
            nullable=False,
        ),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("persisted_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_feature_snapshots_race", "feature_snapshots", ["race_id", "as_of_time"])
    op.create_index(
        "ix_prediction_snapshots_race",
        "prediction_snapshots",
        ["race_id", "as_of_time"],
    )
    op.create_index("ix_recommendations_race", "recommendations", ["race_id", "persisted_at"])

    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        for table_name in IMMUTABLE_TABLES:
            op.execute(
                f"CREATE TRIGGER {table_name}_append_only_update "
                f"BEFORE UPDATE ON {table_name} BEGIN "
                f"SELECT RAISE(ABORT, '{table_name} is append-only'); END;"
            )
            op.execute(
                f"CREATE TRIGGER {table_name}_append_only_delete "
                f"BEFORE DELETE ON {table_name} BEGIN "
                f"SELECT RAISE(ABORT, '{table_name} is append-only'); END;"
            )
    elif bind.dialect.name == "postgresql":
        op.execute(
            "CREATE OR REPLACE FUNCTION keiba_lab_append_only_guard() "
            "RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN "
            "RAISE EXCEPTION '% is append-only', TG_TABLE_NAME; END; $$;"
        )
        for table_name in IMMUTABLE_TABLES:
            op.execute(
                f"CREATE TRIGGER {table_name}_append_only "
                f"BEFORE UPDATE OR DELETE ON {table_name} FOR EACH ROW "
                "EXECUTE FUNCTION keiba_lab_append_only_guard();"
            )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        for table_name in IMMUTABLE_TABLES:
            op.execute(f"DROP TRIGGER IF EXISTS {table_name}_append_only_update")
            op.execute(f"DROP TRIGGER IF EXISTS {table_name}_append_only_delete")
    elif bind.dialect.name == "postgresql":
        for table_name in IMMUTABLE_TABLES:
            op.execute(f"DROP TRIGGER IF EXISTS {table_name}_append_only ON {table_name}")
        op.execute("DROP FUNCTION IF EXISTS keiba_lab_append_only_guard()")

    op.drop_index("ix_recommendations_race", table_name="recommendations")
    op.drop_index("ix_prediction_snapshots_race", table_name="prediction_snapshots")
    op.drop_index("ix_feature_snapshots_race", table_name="feature_snapshots")
    op.drop_index("ix_raw_observations_temporal", table_name="raw_observations")
    op.drop_table("results")
    op.drop_table("recommendations")
    op.drop_table("prediction_snapshots")
    op.drop_table("feature_snapshots")
    op.drop_table("data_snapshots")
    op.drop_table("raw_observations")
    op.drop_table("logic_versions")
    op.drop_table("feature_versions")
    op.drop_table("model_versions")
