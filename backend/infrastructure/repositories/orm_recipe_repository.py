from typing import Any

from sqlalchemy.orm import Session

from backend.domain.entities.recipe import Recipe
from backend.domain.ports.recipe_repository import RecipeRepository
from backend.domain.value_objects.cooking_step import CookingStep
from backend.domain.value_objects.quantity import Quantity
from backend.domain.value_objects.recipe_ingredient import RecipeIngredient
from backend.domain.value_objects.types import (
    ProductId,
    RecipeCategoryId,
    RecipeId,
    UserId,
)
from backend.infrastructure.database.models import (
    CookingStepRow,
    RecipeIngredientRow,
    RecipeRow,
)
from backend.infrastructure.repositories.base import BaseOrmRepository


class OrmRecipeRepository(
    BaseOrmRepository[Recipe, RecipeId],
    RecipeRepository,
):
    _row_class = RecipeRow

    def __init__(self, session: Session) -> None:
        super().__init__(session)

    def _get_entity_id(self, entity: Recipe) -> int:
        return entity.id

    def _wrap_id(self, raw_id: int) -> RecipeId:
        return RecipeId(raw_id)

    @staticmethod
    def _ingredients_to_rows(ingredients: list[RecipeIngredient]) -> list[RecipeIngredientRow]:
        return [
            RecipeIngredientRow(
                product_id=int(ing.product_id) if ing.product_id is not None else None,
                sub_recipe_id=int(ing.sub_recipe_id) if ing.sub_recipe_id is not None else None,
                amount=ing.quantity.amount,
                unit=ing.quantity.unit,
                ingredient_order=ing.order,
            )
            for ing in ingredients
        ]

    @staticmethod
    def _steps_to_rows(steps: list[CookingStep]) -> list[CookingStepRow]:
        return [
            CookingStepRow(step_order=step.order, description=step.description)
            for step in steps
        ]

    def _make_new_row(self, entity: Recipe) -> RecipeRow:
        row = RecipeRow(
            user_id=int(entity.user_id),
            name=entity.name,
            category_id=entity.category_id,
            servings=entity.servings,
            weight=entity.weight,
            total_pieces=entity.total_pieces,
            pieces_per_portion=entity.pieces_per_portion,
        )
        row.ingredients = self._ingredients_to_rows(entity.ingredients)
        row.steps = self._steps_to_rows(entity.steps)
        return row

    def _update_row(self, row: Any, entity: Recipe) -> None:
        row.name = entity.name
        row.category_id = entity.category_id
        row.servings = entity.servings
        row.weight = entity.weight
        row.total_pieces = entity.total_pieces
        row.pieces_per_portion = entity.pieces_per_portion
        row.ingredients = self._ingredients_to_rows(entity.ingredients)
        row.steps = self._steps_to_rows(entity.steps)

    def _row_to_entity(self, row: Any) -> Recipe:
        return Recipe(
            id=RecipeId(row.id),
            name=row.name,
            servings=row.servings,
            ingredients=[
                RecipeIngredient(
                    product_id=ProductId(r.product_id) if r.product_id is not None else None,
                    sub_recipe_id=RecipeId(r.sub_recipe_id) if r.sub_recipe_id is not None else None,
                    quantity=Quantity(r.amount, r.unit),
                    order=r.ingredient_order,
                )
                for r in sorted(row.ingredients, key=lambda i: i.ingredient_order)
            ],
            steps=[
                CookingStep(order=r.step_order, description=r.description)
                for r in sorted(row.steps, key=lambda s: s.step_order)
            ],
            category_id=RecipeCategoryId(row.category_id),
            weight=row.weight,
            user_id=UserId(row.user_id),
            total_pieces=row.total_pieces,
            pieces_per_portion=row.pieces_per_portion,
        )

    def find_all(self, user_id: UserId) -> list[Recipe]:
        return self.find_all_by_user(int(user_id))

    def find_by_category_id(
        self, category_id: RecipeCategoryId, user_id: UserId
    ) -> list[Recipe]:
        rows = (
            self._session.query(RecipeRow)
            .filter(
                RecipeRow.category_id == category_id,
                RecipeRow.user_id == int(user_id),
            )
            .all()
        )
        return [self._row_to_entity(r) for r in rows]

    def find_parents_of(
        self, sub_recipe_id: RecipeId, user_id: UserId
    ) -> list[Recipe]:
        rows = (
            self._session.query(RecipeRow)
            .join(
                RecipeIngredientRow,
                RecipeRow.id == RecipeIngredientRow.recipe_id,
            )
            .filter(
                RecipeIngredientRow.sub_recipe_id == int(sub_recipe_id),
                RecipeRow.user_id == int(user_id),
            )
            .all()
        )
        return [self._row_to_entity(r) for r in rows]
