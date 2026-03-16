"""add ingredient_order to recipe_ingredients

Revision ID: a1b2c3d4e5f6
Revises: 374e6ef29ac2b2c3
Create Date: 2026-03-16 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "374e6ef29ac2b2c3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("recipe_ingredients") as batch_op:
        batch_op.add_column(
            sa.Column("ingredient_order", sa.Integer(), nullable=False, server_default="0")
        )


def downgrade() -> None:
    with op.batch_alter_table("recipe_ingredients") as batch_op:
        batch_op.drop_column("ingredient_order")
