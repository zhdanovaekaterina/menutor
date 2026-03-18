"""add_sub_recipe_support

Revision ID: da00777f78e8
Revises: c3d4e5f6a7b8
Create Date: 2026-03-18 13:13:36.110314

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "da00777f78e8"
down_revision: Union[str, None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    dialect = op.get_context().dialect.name
    if dialect == "sqlite":
        op.execute(
            "INSERT OR IGNORE INTO units (name, unit_group) VALUES ('serv', 'servings')"
        )
    else:
        op.execute(
            "INSERT INTO units (name, unit_group) VALUES ('serv', 'servings') "
            "ON CONFLICT (name) DO NOTHING"
        )

    with op.batch_alter_table("recipe_ingredients", recreate="always") as batch_op:
        batch_op.add_column(
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False)
        )
        batch_op.add_column(
            sa.Column(
                "sub_recipe_id",
                sa.Integer(),
                sa.ForeignKey("recipes.id", ondelete="SET NULL"),
                nullable=True,
            )
        )
        batch_op.alter_column("product_id", existing_type=sa.Integer(), nullable=True)
        batch_op.create_primary_key("pk_recipe_ingredients", ["id"])
        batch_op.create_check_constraint(
            "check_ingredient_xor",
            "(product_id IS NOT NULL AND sub_recipe_id IS NULL) OR "
            "(product_id IS NULL AND sub_recipe_id IS NOT NULL)",
        )


def downgrade() -> None:
    with op.batch_alter_table("recipe_ingredients", recreate="always") as batch_op:
        batch_op.drop_column("sub_recipe_id")
        batch_op.alter_column("product_id", existing_type=sa.Integer(), nullable=False)
        batch_op.drop_column("id")
        batch_op.create_primary_key("pk_recipe_ingredients", ["recipe_id", "product_id"])
    op.execute("DELETE FROM units WHERE name = 'serv'")
