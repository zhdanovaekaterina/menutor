"""add_member_ids_to_menu_slots

Add member_ids column to menu_slots table for Individual Menu Mode.

Revision ID: a9b8c7d6e5f4
Revises: a2b3c4d5e6f7
Create Date: 2026-04-01 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a9b8c7d6e5f4"
down_revision: Union[str, None] = "a2b3c4d5e6f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "menu_slots",
        sa.Column(
            "member_ids",
            sa.String(),
            nullable=False,
            server_default="[]",
        ),
    )


def downgrade() -> None:
    op.drop_column("menu_slots", "member_ids")
