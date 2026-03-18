from backend.domain.ports.product_category_repository import ProductCategoryRepository
from backend.infrastructure.database.models import (
    MenuSlotRow,
    ProductCategoryRow,
    ProductRow,
    RecipeIngredientRow,
)
from backend.infrastructure.repositories.base_category import BaseOrmCategoryRepository


class SqlAlchemyProductCategoryRepository(
    BaseOrmCategoryRepository,
    ProductCategoryRepository,
):
    _cat_class = ProductCategoryRow
    _linked_class = ProductRow
    _linked_fk_col = "category_id"

    def hard_delete(self, category_id: int) -> None:
        product_ids = [
            pid
            for (pid,) in self._session.query(ProductRow.id)
            .filter(ProductRow.category_id == category_id)
            .all()
        ]
        if product_ids:
            self._session.query(RecipeIngredientRow).filter(
                RecipeIngredientRow.product_id.in_(product_ids)
            ).delete(synchronize_session=False)
            self._session.query(MenuSlotRow).filter(
                MenuSlotRow.product_id.in_(product_ids)
            ).delete(synchronize_session=False)
            self._session.query(ProductRow).filter(
                ProductRow.category_id == category_id
            ).delete(synchronize_session=False)
        row = self._session.get(self._cat_class, category_id)
        if row is not None:
            self._session.delete(row)
        self._session.commit()
