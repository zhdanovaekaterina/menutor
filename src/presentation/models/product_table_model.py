from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from src.domain.entities.product import Product

COLUMNS = ["Название", "Категория", "Бренд", "Ед.рецепта", "Ед.покупки", "Цена, руб."]


class ProductTableModel(QAbstractTableModel):
    """Qt-модель таблицы продуктов."""

    def __init__(self, products: list[Product] | None = None) -> None:
        super().__init__()
        self._products: list[Product] = products or []

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
                return product.category
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

    def set_products(self, products: list[Product]) -> None:
        self.beginResetModel()
        self._products = list(products)
        self.endResetModel()

    def product_at(self, row: int) -> Product | None:
        if 0 <= row < len(self._products):
            return self._products[row]
        return None
