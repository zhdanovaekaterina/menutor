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


class SqliteRecipeRepository(
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

    def _make_new_row(self, entity: Recipe) -> RecipeRow:
        row = RecipeRow(
            user_id=int(entity.user_id),
            name=entity.name,
            category_id=entity.category_id,
            servings=entity.servings,
            weight=entity.weight,
        )
        row.ingredients = [
            RecipeIngredientRow(
                product_id=ing.product_id,
                amount=ing.quantity.amount,
                unit=ing.quantity.unit,
            )
            for ing in entity.ingredients
        ]
        row.steps = [
            CookingStepRow(step_order=step.order, description=step.description)
            for step in entity.steps
        ]
        return row

    def _update_row(self, row: Any, entity: Recipe) -> None:
        row.name = entity.name
        row.category_id = entity.category_id
        row.servings = entity.servings
        row.weight = entity.weight
        row.ingredients = [
            RecipeIngredientRow(
                product_id=ing.product_id,
                amount=ing.quantity.amount,
                unit=ing.quantity.unit,
            )
            for ing in entity.ingredients
        ]
        row.steps = [
            CookingStepRow(step_order=step.order, description=step.description)
            for step in entity.steps
        ]

    def _row_to_entity(self, row: Any) -> Recipe:
        return Recipe(
            id=RecipeId(row.id),
            name=row.name,
            servings=row.servings,
            ingredients=[
                RecipeIngredient(
                    product_id=ProductId(r.product_id),
                    quantity=Quantity(r.amount, r.unit),
                )
                for r in row.ingredients
            ],
            steps=[
                CookingStep(order=r.step_order, description=r.description)
                for r in sorted(row.steps, key=lambda s: s.step_order)
            ],
            category_id=RecipeCategoryId(row.category_id),
            weight=row.weight,
            user_id=UserId(row.user_id),
        )

    def find_all(self, user_id: UserId) -> list[Recipe]:
        rows = (
            self._session.query(RecipeRow)
            .filter(RecipeRow.user_id == int(user_id))
            .all()
        )
        return [self._row_to_entity(r) for r in rows]

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
