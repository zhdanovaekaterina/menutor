"""add_preference_recipe_categories

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-04-03 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c2d3e4f5a6b7"
down_revision: Union[str, None] = "b1c2d3e4f5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "preference_recipe_categories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("preference_id", sa.Integer(), nullable=False),
        sa.Column("recipe_category_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["preference_id"], ["preferences.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["recipe_category_id"], ["recipe_categories.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("preference_recipe_categories")
