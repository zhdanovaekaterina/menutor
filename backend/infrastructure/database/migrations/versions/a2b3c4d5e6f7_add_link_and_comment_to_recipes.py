"""add_link_and_comment_to_recipes

Revision ID: a2b3c4d5e6f7
Revises: 0cf76e3bb053
Create Date: 2026-03-27 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a2b3c4d5e6f7'
down_revision: Union[str, None] = '0cf76e3bb053'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("recipes", sa.Column("link", sa.String(), nullable=True))
    op.add_column("recipes", sa.Column("comment", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("recipes", "comment")
    op.drop_column("recipes", "link")
