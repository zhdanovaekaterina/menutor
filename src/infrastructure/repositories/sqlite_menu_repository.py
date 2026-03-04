import sqlite3

from src.domain.entities.menu import MenuSlot, WeeklyMenu
from src.domain.ports.menu_repository import MenuRepository
from src.domain.value_objects.types import MenuId, RecipeId


class SqliteMenuRepository(MenuRepository):
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    # ---- read ----

    def get_by_id(self, id: MenuId) -> WeeklyMenu | None:
        row = self._conn.execute(
            "SELECT id, name FROM menus WHERE id = ?", (id,)
        ).fetchone()
        return self._row_to_entity(row) if row else None

    def find_all(self) -> list[WeeklyMenu]:
        rows = self._conn.execute("SELECT id, name FROM menus").fetchall()
        return [self._row_to_entity(r) for r in rows]

    # ---- write ----

    def save(self, menu: WeeklyMenu) -> WeeklyMenu:
        menu_id: MenuId
        with self._conn:
            if menu.id == 0:
                cursor = self._conn.execute(
                    "INSERT INTO menus (name) VALUES (?)", (menu.name,)
                )
                last_id = cursor.lastrowid
                if last_id is None:
                    raise RuntimeError("INSERT menus did not return lastrowid")
                menu_id = MenuId(last_id)
            else:
                self._conn.execute(
                    "UPDATE menus SET name=? WHERE id=?", (menu.name, menu.id)
                )
                menu_id = menu.id

            self._conn.execute(
                "DELETE FROM menu_slots WHERE menu_id = ?", (menu_id,)
            )
            self._conn.executemany(
                "INSERT INTO menu_slots "
                "(menu_id, day, meal_type, recipe_id, servings_override) "
                "VALUES (?, ?, ?, ?, ?)",
                [
                    (menu_id, s.day, s.meal_type, s.recipe_id, s.servings_override)
                    for s in menu.slots
                ],
            )

        result = self.get_by_id(menu_id)
        if result is None:
            raise RuntimeError(f"Failed to retrieve menu {menu_id} after save")
        return result

    def delete(self, id: MenuId) -> None:
        with self._conn:
            self._conn.execute("DELETE FROM menus WHERE id = ?", (id,))

    # ---- mapping ----

    def _row_to_entity(self, row: sqlite3.Row) -> WeeklyMenu:
        mid = MenuId(row["id"])
        slot_rows = self._conn.execute(
            "SELECT day, meal_type, recipe_id, servings_override "
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
                    recipe_id=RecipeId(r["recipe_id"]),
                    servings_override=r["servings_override"],
                )
                for r in slot_rows
            ],
        )
