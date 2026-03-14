"""drop weight_per_piece_g from products

Revision ID: 374e6ef29ac2b2c3
Revises: b3a1faa2d044
Create Date: 2026-03-15 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "374e6ef29ac2b2c3"
down_revision: Union[str, None] = "b3a1faa2d044"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("products") as batch_op:
        batch_op.drop_column("weight_per_piece_g")


def downgrade() -> None:
    with op.batch_alter_table("products") as batch_op:
        batch_op.add_column(sa.Column("weight_per_piece_g", sa.Float(), nullable=True))
