from src.domain.ports.recipe_category_repository import RecipeCategoryRepository
from src.infrastructure.repositories.base_category import BaseSqliteCategoryRepository


class SqliteRecipeCategoryRepository(BaseSqliteCategoryRepository, RecipeCategoryRepository):
    _table_name = "recipe_categories"
    _usage_query = "SELECT COUNT(*) FROM recipes WHERE category_id = ?"
