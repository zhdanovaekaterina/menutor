from src.domain.entities.product import Product
from src.presentation.models.base_table_model import BaseCrudTableModel
from src.presentation.units import to_display


class ProductTableModel(BaseCrudTableModel[Product]):
    """Qt-модель таблицы продуктов."""

    _columns = ["Название", "Категория", "Бренд", "Поставщик", "Ед.рецепта", "Ед.покупки", "Цена, руб."]

    def _entity_id(self, entity: Product) -> int:
        return entity.id

    def _entity_name(self, entity: Product) -> str:
        return entity.name

    def _display_value(self, entity: Product, column: int) -> str:
        if column == 0:
            return entity.name
        if column == 1:
            return self._category_map.get(entity.category_id, "")
        if column == 2:
            return entity.brand
        if column == 3:
            return entity.supplier
        if column == 4:
            return to_display(entity.recipe_unit)
        if column == 5:
            return to_display(entity.purchase_unit)
        if column == 6:
            return f"{entity.price_per_purchase_unit.amount:.2f}"
        return ""

    def set_products(self, products: list[Product]) -> None:
        self.set_items(products)

    def product_at(self, row: int) -> Product | None:
        return self.item_at(row)
