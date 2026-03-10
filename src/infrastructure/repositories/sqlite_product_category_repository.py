from src.domain.ports.product_category_repository import ProductCategoryRepository
from src.infrastructure.database.models import ProductCategoryRow, ProductRow
from src.infrastructure.repositories.base_category import BaseOrmCategoryRepository


class SqliteProductCategoryRepository(
    BaseOrmCategoryRepository,
    ProductCategoryRepository,
):
    _cat_class = ProductCategoryRow
    _linked_class = ProductRow
    _linked_fk_col = "category_id"
