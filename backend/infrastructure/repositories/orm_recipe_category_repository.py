from backend.domain.ports.recipe_category_repository import RecipeCategoryRepository
from backend.infrastructure.database.models import (
    CookingStepRow,
    MenuSlotRow,
    RecipeCategoryRow,
    RecipeIngredientRow,
    RecipeRow,
)
from backend.infrastructure.repositories.base_category import BaseOrmCategoryRepository


class OrmRecipeCategoryRepository(
    BaseOrmCategoryRepository,
    RecipeCategoryRepository,
):
    _cat_class = RecipeCategoryRow
    _linked_class = RecipeRow
    _linked_fk_col = "category_id"

    def hard_delete(self, category_id: int) -> None:
        recipe_ids = [
            rid
            for (rid,) in self._session.query(RecipeRow.id)
            .filter(RecipeRow.category_id == category_id)
            .all()
        ]
        if recipe_ids:
            self._session.query(RecipeIngredientRow).filter(
                RecipeIngredientRow.recipe_id.in_(recipe_ids)
            ).delete(synchronize_session=False)
            self._session.query(CookingStepRow).filter(
                CookingStepRow.recipe_id.in_(recipe_ids)
            ).delete(synchronize_session=False)
            self._session.query(MenuSlotRow).filter(
                MenuSlotRow.recipe_id.in_(recipe_ids)
            ).delete(synchronize_session=False)
            self._session.query(RecipeRow).filter(
                RecipeRow.category_id == category_id
            ).delete(synchronize_session=False)
        row = self._session.get(self._cat_class, category_id)
        if row is not None:
            self._session.delete(row)
        self._session.commit()
