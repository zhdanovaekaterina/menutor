"""add meal types table and migrate menu slots

Revision ID: a1b2c3d4e5e7
Revises: c2d3e4f5a6b7
Create Date: 2026-04-03 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5e7"
down_revision: Union[str, None] = "c2d3e4f5a6b7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create meal_types table
    op.create_table(
        "meal_types",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("time", sa.String(5), nullable=False),
        sa.Column("is_system", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"),
        sa.UniqueConstraint("user_id", "name", name="uq_meal_types_user_name"),
    )

    # 2. For each existing user — create 3 system types
    conn = op.get_bind()
    users = conn.execute(sa.text("SELECT id FROM users")).fetchall()
    for (user_id,) in users:
        for name, time_str, order in [
            ("Завтрак", "08:00", 0),
            ("Обед", "13:00", 1),
            ("Ужин", "18:00", 2),
        ]:
            conn.execute(
                sa.text(
                    "INSERT INTO meal_types (user_id, name, time, is_system, sort_order) "
                    "VALUES (:uid, :name, :time, true, :order)"
                ),
                {"uid": user_id, "name": name, "time": time_str, "order": order},
            )

    # 3. Handle non-standard types from existing slots
    custom_types = conn.execute(
        sa.text(
            "SELECT DISTINCT m.user_id, ms.meal_type "
            "FROM menu_slots ms "
            "JOIN menus m ON m.id = ms.menu_id "
            "WHERE ms.meal_type NOT IN ('Завтрак', 'Обед', 'Ужин')"
        )
    ).fetchall()
    for user_id, meal_type_name in custom_types:
        conn.execute(
            sa.text(
                "INSERT INTO meal_types (user_id, name, time, is_system, sort_order) "
                "VALUES (:uid, :name, '12:00', 0, 10)"
            ),
            {"uid": user_id, "name": meal_type_name},
        )

    # 4. Add meal_type_id column (nullable first)
    op.add_column("menu_slots", sa.Column("meal_type_id", sa.Integer, nullable=True))

    # 5. Fill meal_type_id from JOIN
    conn.execute(
        sa.text(
            "UPDATE menu_slots SET meal_type_id = ("
            "  SELECT mt.id FROM meal_types mt"
            "  JOIN menus m ON m.user_id = mt.user_id"
            "  WHERE m.id = menu_slots.menu_id"
            "  AND LOWER(mt.name) = LOWER(menu_slots.meal_type)"
            ")"
        )
    )

    # 6. Make not null, add FK, drop old column
    with op.batch_alter_table("menu_slots") as batch_op:
        batch_op.alter_column("meal_type_id", nullable=False)
        batch_op.create_foreign_key(
            "fk_menu_slots_meal_type_id",
            "meal_types",
            ["meal_type_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch_op.drop_column("meal_type")


def downgrade() -> None:
    with op.batch_alter_table("menu_slots") as batch_op:
        batch_op.add_column(sa.Column("meal_type", sa.String, nullable=True))

    conn = op.get_bind()
    conn.execute(
        sa.text(
            "UPDATE menu_slots SET meal_type = ("
            "  SELECT mt.name FROM meal_types mt WHERE mt.id = menu_slots.meal_type_id"
            ")"
        )
    )

    with op.batch_alter_table("menu_slots") as batch_op:
        batch_op.alter_column("meal_type", nullable=False)
        batch_op.drop_constraint("fk_menu_slots_meal_type_id", type_="foreignkey")
        batch_op.drop_column("meal_type_id")

    op.drop_table("meal_types")
