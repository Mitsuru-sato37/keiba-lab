"""Add immutable backtest run, fold, guard, and artifact records."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision = "0004_phase5_backtest_records"
down_revision = "0003_phase3_feature_logic_lineage"
branch_labels = None
depends_on = None

IMMUTABLE_TABLES: Sequence[str] = (
    "backtest_runs",
    "backtest_folds",
    "backtest_guard_results",
    "backtest_artifacts",
)


def upgrade() -> None:
    op.create_table(
        "backtest_runs",
        sa.Column("run_id", sa.String(128), primary_key=True),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("manifest", sa.JSON(), nullable=False),
        sa.Column("manifest_checksum", sa.String(128), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('pending', 'running', 'succeeded', 'invalid')",
            name="ck_backtest_run_status",
        ),
    )
    op.create_table(
        "backtest_folds",
        sa.Column("fold_id", sa.String(128), primary_key=True),
        sa.Column(
            "run_id",
            sa.String(128),
            sa.ForeignKey("backtest_runs.run_id"),
            nullable=False,
        ),
        sa.Column("test_year", sa.Integer(), nullable=False),
        sa.Column("training_years", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("manifest", sa.JSON(), nullable=False),
        sa.Column("manifest_checksum", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('pending', 'running', 'succeeded', 'invalid')",
            name="ck_backtest_fold_status",
        ),
    )
    op.create_table(
        "backtest_guard_results",
        sa.Column("guard_result_id", sa.String(128), primary_key=True),
        sa.Column(
            "run_id",
            sa.String(128),
            sa.ForeignKey("backtest_runs.run_id"),
            nullable=False,
        ),
        sa.Column(
            "fold_id",
            sa.String(128),
            sa.ForeignKey("backtest_folds.fold_id"),
        ),
        sa.Column("guard_id", sa.String(128), nullable=False),
        sa.Column("guard_version", sa.String(128), nullable=False),
        sa.Column("status", sa.String(8), nullable=False),
        sa.Column("checked_input_ids", sa.JSON(), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('pass', 'fail')",
            name="ck_backtest_guard_status",
        ),
    )
    op.create_table(
        "backtest_artifacts",
        sa.Column("artifact_id", sa.String(128), primary_key=True),
        sa.Column(
            "run_id",
            sa.String(128),
            sa.ForeignKey("backtest_runs.run_id"),
            nullable=False,
        ),
        sa.Column(
            "fold_id",
            sa.String(128),
            sa.ForeignKey("backtest_folds.fold_id"),
        ),
        sa.Column("artifact_kind", sa.String(64), nullable=False),
        sa.Column("artifact_ref_id", sa.String(128), nullable=False),
        sa.Column("manifest", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_backtest_folds_run", "backtest_folds", ["run_id", "test_year"])
    op.create_index(
        "ix_backtest_guards_run",
        "backtest_guard_results",
        ["run_id", "guard_id"],
    )
    op.create_index(
        "ix_backtest_artifacts_run",
        "backtest_artifacts",
        ["run_id", "artifact_kind"],
    )

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

    op.drop_index("ix_backtest_artifacts_run", table_name="backtest_artifacts")
    op.drop_index("ix_backtest_guards_run", table_name="backtest_guard_results")
    op.drop_index("ix_backtest_folds_run", table_name="backtest_folds")
    op.drop_table("backtest_artifacts")
    op.drop_table("backtest_guard_results")
    op.drop_table("backtest_folds")
    op.drop_table("backtest_runs")
