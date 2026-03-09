import sqlite3

from src.domain.entities.recipe import Recipe
from src.domain.exceptions import RepositoryError
from src.domain.ports.recipe_repository import RecipeRepository
from src.domain.value_objects.cooking_step import CookingStep
from src.domain.value_objects.quantity import Quantity
from src.domain.value_objects.recipe_ingredient import RecipeIngredient
from src.domain.value_objects.types import ProductId, RecipeCategoryId, RecipeId
from src.infrastructure.repositories.base import BaseSqliteRepository


class SqliteRecipeRepository(
    BaseSqliteRepository[Recipe, RecipeId],
    RecipeRepository,
):
    _table_name = "recipes"
    _columns = "id, name, category_id, dietary_tags, servings, weight"

    def _get_entity_id(self, entity: Recipe) -> int:
        return entity.id

    def _wrap_id(self, raw_id: int) -> RecipeId:
        return RecipeId(raw_id)

    def _insert(self, entity: Recipe) -> int:
        cursor = self._conn.execute(
            "INSERT INTO recipes (name, category_id, servings, weight) "
            "VALUES (?, ?, ?, ?)",
            (entity.name, entity.category_id, entity.servings, entity.weight),
        )
        last_id = cursor.lastrowid
        if last_id is None:
            raise RepositoryError("INSERT recipes did not return lastrowid")
        return last_id

    def _update(self, entity: Recipe) -> None:
        self._conn.execute(
            "UPDATE recipes SET name=?, category_id=?, servings=?, weight=? "
            "WHERE id=?",
            (entity.name, entity.category_id, entity.servings, entity.weight, entity.id),
        )

    def _save_children(self, entity_id: RecipeId, entity: Recipe) -> None:
        self._conn.execute(
            "DELETE FROM recipe_ingredients WHERE recipe_id = ?", (entity_id,)
        )
        self._conn.executemany(
            "INSERT INTO recipe_ingredients (recipe_id, product_id, amount, unit) "
            "VALUES (?, ?, ?, ?)",
            [
                (entity_id, ing.product_id, ing.quantity.amount, ing.quantity.unit)
                for ing in entity.ingredients
            ],
        )
        self._conn.execute(
            "DELETE FROM cooking_steps WHERE recipe_id = ?", (entity_id,)
        )
        self._conn.executemany(
            "INSERT INTO cooking_steps (recipe_id, step_order, description) "
            "VALUES (?, ?, ?)",
            [(entity_id, step.order, step.description) for step in entity.steps],
        )

    def _row_to_entity(self, row: sqlite3.Row) -> Recipe:
        rid = RecipeId(row["id"])
        ingredient_rows = self._conn.execute(
            "SELECT product_id, amount, unit FROM recipe_ingredients "
            "WHERE recipe_id = ?",
            (rid,),
        ).fetchall()
        step_rows = self._conn.execute(
            "SELECT step_order, description FROM cooking_steps "
            "WHERE recipe_id = ? ORDER BY step_order",
            (rid,),
        ).fetchall()
        return Recipe(
            id=rid,
            name=row["name"],
            servings=row["servings"],
            ingredients=[
                RecipeIngredient(
                    product_id=ProductId(r["product_id"]),
                    quantity=Quantity(r["amount"], r["unit"]),
                )
                for r in ingredient_rows
            ],
            steps=[
                CookingStep(order=r["step_order"], description=r["description"])
                for r in step_rows
            ],
            category_id=RecipeCategoryId(row["category_id"]),
            weight=row["weight"],
        )

    def find_by_category_id(self, category_id: RecipeCategoryId) -> list[Recipe]:
        rows = self._conn.execute(
            f"SELECT {self._columns} FROM recipes WHERE category_id = ?",
            (category_id,),
        ).fetchall()
        return [self._row_to_entity(r) for r in rows]
