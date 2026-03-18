"""seed tsp and tbsp units

Revision ID: c3d4e5f6a7b8
Revises: b5c6d7e8f9a0
Create Date: 2026-03-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, None] = "b5c6d7e8f9a0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        op.execute(
            "INSERT OR IGNORE INTO units (name, unit_group) VALUES "
            "('tsp', 'volume'), ('tbsp', 'volume')"
        )
    else:
        op.execute(
            "INSERT INTO units (name, unit_group) VALUES "
            "('tsp', 'volume'), ('tbsp', 'volume') "
            "ON CONFLICT (name) DO NOTHING"
        )


def downgrade() -> None:
    op.execute("DELETE FROM units WHERE name IN ('tsp', 'tbsp')")
