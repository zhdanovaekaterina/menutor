"""add_category_color

Revision ID: 0cf76e3bb053
Revises: f1a2b3c4d5e6
Create Date: 2026-03-26 09:03:46.022263

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '0cf76e3bb053'
down_revision: Union[str, None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("recipe_categories", sa.Column("color", sa.String(7), nullable=True))
    op.add_column("product_categories", sa.Column("color", sa.String(7), nullable=True))


def downgrade() -> None:
    op.drop_column("product_categories", "color")
    op.drop_column("recipe_categories", "color")
