import sqlite3

from src.domain.entities.menu import MenuSlot, WeeklyMenu
from src.domain.exceptions import RepositoryError
from src.domain.ports.menu_repository import MenuRepository
from src.domain.value_objects.types import MenuId, ProductId, RecipeId
from src.infrastructure.repositories.base import BaseSqliteRepository


class SqliteMenuRepository(
    BaseSqliteRepository[WeeklyMenu, MenuId],
    MenuRepository,
):
    _table_name = "menus"
    _columns = "id, name"

    def _get_entity_id(self, entity: WeeklyMenu) -> int:
        return entity.id

    def _wrap_id(self, raw_id: int) -> MenuId:
        return MenuId(raw_id)

    def _insert(self, entity: WeeklyMenu) -> int:
        cursor = self._conn.execute(
            "INSERT INTO menus (name) VALUES (?)", (entity.name,)
        )
        last_id = cursor.lastrowid
        if last_id is None:
            raise RepositoryError("INSERT menus did not return lastrowid")
        return last_id

    def _update(self, entity: WeeklyMenu) -> None:
        self._conn.execute(
            "UPDATE menus SET name=? WHERE id=?", (entity.name, entity.id)
        )

    def _save_children(self, entity_id: MenuId, entity: WeeklyMenu) -> None:
        self._conn.execute(
            "DELETE FROM menu_slots WHERE menu_id = ?", (entity_id,)
        )
        self._conn.executemany(
            "INSERT INTO menu_slots "
            "(menu_id, day, meal_type, recipe_id, product_id, quantity, unit, servings_override) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (entity_id, s.day, s.meal_type, s.recipe_id, s.product_id,
                 s.quantity, s.unit, s.servings_override)
                for s in entity.slots
            ],
        )

    def _row_to_entity(self, row: sqlite3.Row) -> WeeklyMenu:
        mid = MenuId(row["id"])
        slot_rows = self._conn.execute(
            "SELECT day, meal_type, recipe_id, product_id, quantity, unit, servings_override "
            "FROM menu_slots WHERE menu_id = ?",
            (mid,),
        ).fetchall()
        return WeeklyMenu(
            id=mid,
            name=row["name"],
            slots=[
                MenuSlot(
                    day=r["day"],
                    meal_type=r["meal_type"],
                    recipe_id=RecipeId(r["recipe_id"]) if r["recipe_id"] is not None else None,
                    product_id=ProductId(r["product_id"]) if r["product_id"] is not None else None,
                    quantity=r["quantity"],
                    unit=r["unit"],
                    servings_override=r["servings_override"],
                )
                for r in slot_rows
            ],
        )
