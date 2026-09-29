"""Create Phase 1 append-only schema."""

from alembic import op
from keiba_lab.persistence.schema import metadata

revision = "20260929_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    metadata.create_all(op.get_bind())


def downgrade() -> None:
    metadata.drop_all(op.get_bind())
