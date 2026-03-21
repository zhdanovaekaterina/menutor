"""add_shopping_lists

Create shopping_lists and shopping_list_items tables for saved shopping lists.

Revision ID: e1f2a3b4c5d6
Revises: 94b6b0751ebe
Create Date: 2026-03-21 10:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e1f2a3b4c5d6"
down_revision: Union[str, None] = "94b6b0751ebe"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "shopping_lists",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("source_menu_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["source_menu_id"], ["menus.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "shopping_list_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("shopping_list_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=True),
        sa.Column("product_name", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("quantity_amount", sa.Float(), nullable=False),
        sa.Column("quantity_unit", sa.String(), nullable=False),
        sa.Column("buy_quantity_amount", sa.Float(), nullable=False),
        sa.Column("buy_quantity_unit", sa.String(), nullable=False),
        sa.Column(
            "buy_quantity_overridden",
            sa.Boolean(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("recipe_quantity_amount", sa.Float(), nullable=True),
        sa.Column("recipe_quantity_unit", sa.String(), nullable=True),
        sa.Column("cost_amount", sa.Float(), nullable=False),
        sa.Column(
            "cost_currency", sa.String(), nullable=False, server_default="RUB"
        ),
        sa.Column(
            "purchased", sa.Boolean(), nullable=False, server_default="0"
        ),
        sa.Column(
            "item_order", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.ForeignKeyConstraint(
            ["shopping_list_id"], ["shopping_lists.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["product_id"], ["products.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("shopping_list_items")
    op.drop_table("shopping_lists")
