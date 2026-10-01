"""Add immutable ingestion batch records for idempotent promotion."""

import sqlalchemy as sa
from alembic import op

revision = "0002_phase2_ingestion_batches"
down_revision = "0001_phase1_data_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ingestion_batches",
        sa.Column("batch_id", sa.String(128), primary_key=True),
        sa.Column("provider", sa.String(128), nullable=False),
        sa.Column("provider_version", sa.String(128), nullable=False),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("content_checksum", sa.String(128), nullable=False),
        sa.Column("record_count", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("status IN ('PROMOTED')", name="ck_ingestion_batch_status"),
    )

    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        op.execute(
            "CREATE TRIGGER ingestion_batches_append_only_update "
            "BEFORE UPDATE ON ingestion_batches BEGIN "
            "SELECT RAISE(ABORT, 'ingestion_batches is append-only'); END;"
        )
        op.execute(
            "CREATE TRIGGER ingestion_batches_append_only_delete "
            "BEFORE DELETE ON ingestion_batches BEGIN "
            "SELECT RAISE(ABORT, 'ingestion_batches is append-only'); END;"
        )
    elif bind.dialect.name == "postgresql":
        op.execute(
            "CREATE TRIGGER ingestion_batches_append_only "
            "BEFORE UPDATE OR DELETE ON ingestion_batches FOR EACH ROW "
            "EXECUTE FUNCTION keiba_lab_append_only_guard();"
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        op.execute("DROP TRIGGER IF EXISTS ingestion_batches_append_only_update")
        op.execute("DROP TRIGGER IF EXISTS ingestion_batches_append_only_delete")
    elif bind.dialect.name == "postgresql":
        op.execute("DROP TRIGGER IF EXISTS ingestion_batches_append_only ON ingestion_batches")
    op.drop_table("ingestion_batches")
