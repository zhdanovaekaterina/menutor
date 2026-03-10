from backend.domain.ports.recipe_category_repository import RecipeCategoryRepository
from backend.infrastructure.database.models import RecipeCategoryRow, RecipeRow
from backend.infrastructure.repositories.base_category import BaseOrmCategoryRepository


class SqliteRecipeCategoryRepository(
    BaseOrmCategoryRepository,
    RecipeCategoryRepository,
):
    _cat_class = RecipeCategoryRow
    _linked_class = RecipeRow
    _linked_fk_col = "category_id"
