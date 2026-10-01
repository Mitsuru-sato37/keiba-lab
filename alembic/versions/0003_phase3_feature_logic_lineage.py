"""Require logic lineage on persisted feature snapshots."""

import sqlalchemy as sa
from alembic import op

revision = "0003_phase3_feature_logic_lineage"
down_revision = "0002_phase2_ingestion_batches"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table("alembic_version") as batch_op:
            batch_op.alter_column(
                "version_num",
                existing_type=sa.String(32),
                type_=sa.String(64),
                existing_nullable=False,
            )
    else:
        op.alter_column(
            "alembic_version",
            "version_num",
            existing_type=sa.String(32),
            type_=sa.String(64),
            existing_nullable=False,
        )

    column = sa.Column("logic_version_id", sa.String(128), nullable=False)
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table("feature_snapshots") as batch_op:
            batch_op.add_column(column)
            batch_op.create_foreign_key(
                "fk_feature_snapshots_logic_version_id",
                "logic_versions",
                ["logic_version_id"],
                ["version_id"],
            )
    else:
        op.add_column("feature_snapshots", column)
        op.create_foreign_key(
            "fk_feature_snapshots_logic_version_id",
            "feature_snapshots",
            "logic_versions",
            ["logic_version_id"],
            ["version_id"],
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table("feature_snapshots") as batch_op:
            batch_op.drop_constraint("fk_feature_snapshots_logic_version_id", type_="foreignkey")
            batch_op.drop_column("logic_version_id")
    else:
        op.drop_constraint(
            "fk_feature_snapshots_logic_version_id",
            "feature_snapshots",
            type_="foreignkey",
        )
        op.drop_column("feature_snapshots", "logic_version_id")
