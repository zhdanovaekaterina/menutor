import sqlite3

from src.domain.entities.recipe import Recipe
from src.domain.ports.recipe_repository import RecipeRepository
from src.domain.value_objects.cooking_step import CookingStep
from src.domain.value_objects.quantity import Quantity
from src.domain.value_objects.recipe_ingredient import RecipeIngredient
from src.domain.value_objects.types import ProductId, RecipeCategoryId, RecipeId


class SqliteRecipeRepository(RecipeRepository):
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    # ---- read ----

    def get_by_id(self, id: RecipeId) -> Recipe | None:
        row = self._conn.execute(
            "SELECT * FROM recipes WHERE id = ?", (id,),
        ).fetchone()
        return self._row_to_entity(row) if row else None

    def find_by_category_id(self, category_id: RecipeCategoryId) -> list[Recipe]:
        rows = self._conn.execute(
            "SELECT * FROM recipes WHERE category_id = ?", (category_id,),
        ).fetchall()
        return [self._row_to_entity(r) for r in rows]

    def find_all(self) -> list[Recipe]:
        rows = self._conn.execute("SELECT * FROM recipes").fetchall()
        return [self._row_to_entity(r) for r in rows]

    # ---- write ----

    def save(self, recipe: Recipe) -> Recipe:
        recipe_id: RecipeId
        with self._conn:
            if recipe.id == 0:
                cursor = self._conn.execute(
                    "INSERT INTO recipes (name, category_id, servings) "
                    "VALUES (?, ?, ?)",
                    (
                        recipe.name,
                        recipe.category_id,
                        recipe.servings,
                    ),
                )
                last_id = cursor.lastrowid
                if last_id is None:
                    raise RuntimeError("INSERT recipes did not return lastrowid")
                recipe_id = RecipeId(last_id)
            else:
                self._conn.execute(
                    "UPDATE recipes SET name=?, category_id=?, servings=? "
                    "WHERE id=?",
                    (
                        recipe.name,
                        recipe.category_id,
                        recipe.servings,
                        recipe.id,
                    ),
                )
                recipe_id = recipe.id

            # Replace ingredients and steps atomically
            self._conn.execute(
                "DELETE FROM recipe_ingredients WHERE recipe_id = ?", (recipe_id,)
            )
            self._conn.executemany(
                "INSERT INTO recipe_ingredients (recipe_id, product_id, amount, unit) "
                "VALUES (?, ?, ?, ?)",
                [
                    (recipe_id, ing.product_id, ing.quantity.amount, ing.quantity.unit)
                    for ing in recipe.ingredients
                ],
            )
            self._conn.execute(
                "DELETE FROM cooking_steps WHERE recipe_id = ?", (recipe_id,)
            )
            self._conn.executemany(
                "INSERT INTO cooking_steps (recipe_id, step_order, description) "
                "VALUES (?, ?, ?)",
                [(recipe_id, step.order, step.description) for step in recipe.steps],
            )

        result = self.get_by_id(recipe_id)
        if result is None:
            raise RuntimeError(f"Failed to retrieve recipe {recipe_id} after save")
        return result

    def delete(self, id: RecipeId) -> None:
        with self._conn:
            self._conn.execute("DELETE FROM recipes WHERE id = ?", (id,))

    # ---- mapping ----

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
        )
