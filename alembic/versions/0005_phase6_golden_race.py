"""Persist Phase 6 Golden Race artifacts, traces, market inputs, and evaluations."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision = "0005_phase6_golden_race"
down_revision = "0004_phase5_backtest_records"
branch_labels = None
depends_on = None

IMMUTABLE_TABLES: Sequence[str] = (
    "calculation_artifacts",
    "logic_traces",
    "simulations",
    "simulation_results",
    "odds_snapshots",
    "bet_candidates",
    "recommendation_items",
    "evaluations",
)


def upgrade() -> None:
    op.create_table(
        "calculation_artifacts",
        sa.Column("artifact_id", sa.String(192), primary_key=True),
        sa.Column("run_id", sa.String(128), nullable=False),
        sa.Column("race_id", sa.String(128), nullable=False),
        sa.Column("stage", sa.String(64), nullable=False),
        sa.Column("output", sa.JSON(), nullable=False),
        sa.Column("lineage", sa.JSON(), nullable=False),
        sa.Column("checksum", sa.String(128), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "logic_traces",
        sa.Column("trace_id", sa.String(192), primary_key=True),
        sa.Column("run_id", sa.String(128), nullable=False),
        sa.Column("race_id", sa.String(128), nullable=False),
        sa.Column("stage", sa.String(64), nullable=False),
        sa.Column("stage_order", sa.Integer(), nullable=False),
        sa.Column(
            "artifact_ref_id",
            sa.String(192),
            sa.ForeignKey("calculation_artifacts.artifact_id"),
            nullable=False,
        ),
        sa.Column("input_ids", sa.JSON(), nullable=False),
        sa.Column("output", sa.JSON(), nullable=False),
        sa.Column("data_snapshot_id", sa.String(128), nullable=False),
        sa.Column("feature_version_id", sa.String(128), nullable=False),
        sa.Column("model_version_id", sa.String(128), nullable=False),
        sa.Column("logic_version_id", sa.String(128), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("error", sa.String(512)),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_ms", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "simulations",
        sa.Column("simulation_id", sa.String(128), primary_key=True),
        sa.Column("run_id", sa.String(128), nullable=False),
        sa.Column("race_id", sa.String(128), nullable=False),
        sa.Column("seed", sa.Integer(), nullable=False),
        sa.Column("logic_version_id", sa.String(128), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "simulation_results",
        sa.Column("simulation_result_id", sa.String(128), primary_key=True),
        sa.Column(
            "simulation_id",
            sa.String(128),
            sa.ForeignKey("simulations.simulation_id"),
            nullable=False,
        ),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "odds_snapshots",
        sa.Column("odds_snapshot_id", sa.String(128), primary_key=True),
        sa.Column("race_id", sa.String(128), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("as_of_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("coverage_status", sa.String(32), nullable=False),
        sa.Column("odds", sa.JSON(), nullable=False),
        sa.Column("data_snapshot_id", sa.String(128), nullable=False),
        sa.Column("logic_version_id", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "bet_candidates",
        sa.Column("candidate_id", sa.String(128), primary_key=True),
        sa.Column("race_id", sa.String(128), nullable=False),
        sa.Column("prediction_snapshot_id", sa.String(128), nullable=False),
        sa.Column(
            "odds_snapshot_id",
            sa.String(128),
            sa.ForeignKey("odds_snapshots.odds_snapshot_id"),
            nullable=False,
        ),
        sa.Column("bet_type", sa.String(32), nullable=False),
        sa.Column("combination", sa.String(128), nullable=False),
        sa.Column("model_probability", sa.Float(), nullable=False),
        sa.Column("odds", sa.Float(), nullable=False),
        sa.Column("expected_value", sa.Float(), nullable=False),
        sa.Column("uncertainty", sa.Float(), nullable=False),
        sa.Column("logic_version_id", sa.String(128), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "recommendation_items",
        sa.Column("recommendation_item_id", sa.String(128), primary_key=True),
        sa.Column(
            "recommendation_id",
            sa.String(128),
            sa.ForeignKey("recommendations.recommendation_id"),
            nullable=False,
        ),
        sa.Column(
            "candidate_id",
            sa.String(128),
            sa.ForeignKey("bet_candidates.candidate_id"),
            nullable=False,
        ),
        sa.Column("stake_yen", sa.Integer(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "evaluations",
        sa.Column("evaluation_id", sa.String(128), primary_key=True),
        sa.Column("race_id", sa.String(128), nullable=False),
        sa.Column(
            "recommendation_id",
            sa.String(128),
            sa.ForeignKey("recommendations.recommendation_id"),
            nullable=False,
        ),
        sa.Column("prediction_metrics", sa.JSON(), nullable=False),
        sa.Column("betting_metrics", sa.JSON()),
        sa.Column("odds_coverage_status", sa.String(32), nullable=False),
        sa.Column("logic_version_id", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_calculation_artifacts_run", "calculation_artifacts", ["run_id", "race_id"])
    op.create_index("ix_logic_traces_run", "logic_traces", ["run_id", "race_id", "stage_order"])
    op.create_index("ix_simulations_race", "simulations", ["race_id", "created_at"])
    op.create_index("ix_odds_snapshots_race", "odds_snapshots", ["race_id", "as_of_time"])
    op.create_index("ix_bet_candidates_race", "bet_candidates", ["race_id", "odds_snapshot_id"])
    op.create_index("ix_evaluations_race", "evaluations", ["race_id", "created_at"])

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

    op.drop_index("ix_evaluations_race", table_name="evaluations")
    op.drop_index("ix_bet_candidates_race", table_name="bet_candidates")
    op.drop_index("ix_odds_snapshots_race", table_name="odds_snapshots")
    op.drop_index("ix_simulations_race", table_name="simulations")
    op.drop_index("ix_logic_traces_run", table_name="logic_traces")
    op.drop_index("ix_calculation_artifacts_run", table_name="calculation_artifacts")
    op.drop_table("evaluations")
    op.drop_table("recommendation_items")
    op.drop_table("bet_candidates")
    op.drop_table("odds_snapshots")
    op.drop_table("simulation_results")
    op.drop_table("simulations")
    op.drop_table("logic_traces")
    op.drop_table("calculation_artifacts")
