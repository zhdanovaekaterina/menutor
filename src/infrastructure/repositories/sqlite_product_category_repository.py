from src.domain.ports.product_category_repository import ProductCategoryRepository
from src.infrastructure.repositories.base_category import BaseSqliteCategoryRepository


class SqliteProductCategoryRepository(BaseSqliteCategoryRepository, ProductCategoryRepository):
    _table_name = "product_categories"
    _usage_query = "SELECT COUNT(*) FROM products WHERE category_id = ?"
