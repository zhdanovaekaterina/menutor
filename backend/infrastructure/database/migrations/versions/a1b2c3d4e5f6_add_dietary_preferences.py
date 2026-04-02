"""add_dietary_preferences

Add preference tables (preferences, preference_categories, preference_products,
family_member_preferences) and migrate dietary_restrictions into comment.

Revision ID: a1b2c3d4e5f6
Revises: f1a2b3c4d5e6
Create Date: 2026-04-02 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "f1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create preferences table
    op.create_table(
        "preferences",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("mode", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # 2. Create preference_categories table
    op.create_table(
        "preference_categories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("preference_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["preference_id"], ["preferences.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["category_id"], ["product_categories.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # 3. Create preference_products table
    op.create_table(
        "preference_products",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("preference_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["preference_id"], ["preferences.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # 4. Create family_member_preferences join table
    op.create_table(
        "family_member_preferences",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("family_member_id", sa.Integer(), nullable=False),
        sa.Column("preference_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["family_member_id"], ["family_members.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["preference_id"], ["preferences.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # 5. Merge dietary_restrictions into comment, then drop the column
    op.execute("""
        UPDATE family_members
        SET comment = CASE
            WHEN comment != '' AND dietary_restrictions != ''
                THEN comment || '\n' || dietary_restrictions
            WHEN dietary_restrictions != ''
                THEN dietary_restrictions
            ELSE comment
        END
        WHERE dietary_restrictions != ''
    """)
    op.drop_column("family_members", "dietary_restrictions")


def downgrade() -> None:
    # Re-add dietary_restrictions column (empty by default)
    op.add_column(
        "family_members",
        sa.Column(
            "dietary_restrictions",
            sa.String(),
            nullable=False,
            server_default="",
        ),
    )

    # Drop tables in reverse order (child tables first)
    op.drop_table("family_member_preferences")
    op.drop_table("preference_products")
    op.drop_table("preference_categories")
    op.drop_table("preferences")
