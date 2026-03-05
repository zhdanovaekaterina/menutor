from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from src.domain.entities.product import Product

COLUMNS = ["Название", "Категория", "Бренд", "Ед.рецепта", "Ед.покупки", "Цена, руб."]


class ProductTableModel(QAbstractTableModel):
    """Qt-модель таблицы продуктов."""

    def __init__(self, products: list[Product] | None = None) -> None:
        super().__init__()
        self._all_products: list[Product] = products or []
        self._products: list[Product] = list(self._all_products)
        self._category_map: dict[int, str] = {}

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._products)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(COLUMNS)

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> object:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return COLUMNS[section]
        return None

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> object:
        if not index.isValid() or not (0 <= index.row() < len(self._products)):
            return None
        product = self._products[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            col = index.column()
            if col == 0:
                return product.name
            if col == 1:
                return self._category_map.get(product.category_id, "")
            if col == 2:
                return product.brand
            if col == 3:
                return product.recipe_unit
            if col == 4:
                return product.purchase_unit
            if col == 5:
                return f"{product.price_per_purchase_unit.amount:.2f}"
        if role == Qt.ItemDataRole.UserRole:
            return product.id
        return None

    def set_category_map(self, category_map: dict[int, str]) -> None:
        self._category_map = category_map

    def set_products(self, products: list[Product]) -> None:
        self.beginResetModel()
        self._all_products = list(products)
        self._products = list(products)
        self.endResetModel()

    def filter(self, query: str) -> None:
        q = query.strip().lower()
        self.beginResetModel()
        self._products = (
            self._all_products
            if not q
            else [p for p in self._all_products if q in p.name.lower()]
        )
        self.endResetModel()

    def product_at(self, row: int) -> Product | None:
        if 0 <= row < len(self._products):
            return self._products[row]
        return None
