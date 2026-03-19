"""add_pieces_mode_fields

Adds total_pieces, pieces_per_portion to recipes and pieces_override to menu_slots.

Revision ID: 94b6b0751ebe
Revises: da00777f78e8
Create Date: 2026-03-20 00:40:33.115900

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '94b6b0751ebe'
down_revision: Union[str, None] = 'da00777f78e8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("recipes", sa.Column("total_pieces", sa.Integer(), nullable=True))
    op.add_column("recipes", sa.Column("pieces_per_portion", sa.Integer(), nullable=True))
    op.add_column("menu_slots", sa.Column("pieces_override", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("menu_slots", "pieces_override")
    op.drop_column("recipes", "pieces_per_portion")
    op.drop_column("recipes", "total_pieces")
