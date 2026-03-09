"""Tests for ShoppingListView — product combo, shopping list rendering, summary."""

from decimal import Decimal

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from src.domain.entities.product import Product
from src.domain.entities.shopping_list import ShoppingList, ShoppingListItem
from src.domain.value_objects.money import Money
from src.domain.value_objects.quantity import Quantity
from src.domain.value_objects.types import ProductCategoryId, ProductId
from src.presentation.views.shopping_list_view import ShoppingListView


def _product(id: int = 1, name: str = "Мука", unit: str = "g") -> Product:
    return Product(
        id=ProductId(id),
        name=name,
        recipe_unit=unit,
        purchase_unit="kg",
        price_per_purchase_unit=Money(Decimal("80")),
        category_id=ProductCategoryId(1),
    )


def _shopping_list() -> ShoppingList:
    return ShoppingList(items=[
        ShoppingListItem(
            product_id=ProductId(1),
            product_name="Мука",
            category="Бакалея",
            quantity=Quantity(2.0, "kg"),
            cost=Money(Decimal("160")),
        ),
        ShoppingListItem(
            product_id=ProductId(2),
            product_name="Молоко",
            category="Молочные",
            quantity=Quantity(1.5, "l"),
            cost=Money(Decimal("135")),
        ),
    ])


class TestShoppingListViewSetProducts:
    def test_populates_combo(self, qapp: QApplication) -> None:
        view = ShoppingListView()
        view.set_products([_product(1, "Мука"), _product(2, "Сахар")])
        assert view._add_product_combo.count() == 2

    def test_combo_item_data_is_product_id(self, qapp: QApplication) -> None:
        view = ShoppingListView()
        view.set_products([_product(42, "Тест")])
        assert view._add_product_combo.itemData(0) == ProductId(42)

    def test_replaces_previous_products(self, qapp: QApplication) -> None:
        view = ShoppingListView()
        view.set_products([_product(1), _product(2)])
        view.set_products([_product(3, "Один")])
        assert view._add_product_combo.count() == 1

    def test_unit_label_updates_on_combo_change(self, qapp: QApplication) -> None:
        view = ShoppingListView()
        view.set_products([_product(1, "Мука", "g"), _product(2, "Молоко", "ml")])
        view._add_product_combo.setCurrentIndex(1)
        assert view._add_unit_label.text() == "мл"


class TestShoppingListViewSetShoppingList:
    def test_renders_items(self, qapp: QApplication) -> None:
        view = ShoppingListView()
        sl = _shopping_list()
        view.set_shopping_list(sl)
        # 2 category headers + 2 data rows = 4
        assert view._table.rowCount() == 4

    def test_renders_category_headers(self, qapp: QApplication) -> None:
        view = ShoppingListView()
        sl = _shopping_list()
        view.set_shopping_list(sl)
        # First row is a category header (Бакалея)
        header_item = view._table.item(0, 0)
        assert header_item is not None
        assert "Бакалея" in header_item.text()

    def test_renders_product_name(self, qapp: QApplication) -> None:
        view = ShoppingListView()
        sl = _shopping_list()
        view.set_shopping_list(sl)
        # Row 1 = first data row (after header)
        name_item = view._table.item(1, 1)
        assert name_item is not None
        assert name_item.text() == "Мука"

    def test_stores_product_id_in_user_role(self, qapp: QApplication) -> None:
        view = ShoppingListView()
        sl = _shopping_list()
        view.set_shopping_list(sl)
        name_item = view._table.item(1, 1)
        assert name_item is not None
        assert name_item.data(Qt.ItemDataRole.UserRole) == 1

    def test_renders_quantity_with_unit(self, qapp: QApplication) -> None:
        view = ShoppingListView()
        sl = _shopping_list()
        view.set_shopping_list(sl)
        qty_item = view._table.item(1, 2)
        assert qty_item is not None
        assert "2.00" in qty_item.text()
        assert "кг" in qty_item.text()

    def test_renders_cost(self, qapp: QApplication) -> None:
        view = ShoppingListView()
        sl = _shopping_list()
        view.set_shopping_list(sl)
        cost_item = view._table.item(1, 3)
        assert cost_item is not None
        assert cost_item.text() == "160.00"

    def test_renders_checkbox_unchecked(self, qapp: QApplication) -> None:
        view = ShoppingListView()
        sl = _shopping_list()
        view.set_shopping_list(sl)
        check_item = view._table.item(1, 0)
        assert check_item is not None
        assert check_item.checkState() == Qt.CheckState.Unchecked

    def test_renders_checkbox_checked_for_purchased(self, qapp: QApplication) -> None:
        view = ShoppingListView()
        sl = ShoppingList(items=[
            ShoppingListItem(
                product_id=ProductId(1),
                product_name="Мука",
                category="Бакалея",
                quantity=Quantity(1.0, "kg"),
                cost=Money(Decimal("80")),
                purchased=True,
            ),
        ])
        view.set_shopping_list(sl)
        check_item = view._table.item(1, 0)
        assert check_item is not None
        assert check_item.checkState() == Qt.CheckState.Checked


class TestShoppingListViewSummary:
    def test_total_label(self, qapp: QApplication) -> None:
        view = ShoppingListView()
        sl = _shopping_list()
        view.set_shopping_list(sl)
        assert "295.00" in view._total_label.text()

    def test_items_count_label(self, qapp: QApplication) -> None:
        view = ShoppingListView()
        sl = _shopping_list()
        view.set_shopping_list(sl)
        assert "2" in view._items_label.text()

    def test_progress_bar_starts_at_zero(self, qapp: QApplication) -> None:
        view = ShoppingListView()
        sl = _shopping_list()
        view.set_shopping_list(sl)
        assert view._progress_bar.value() == 0

    def test_empty_list(self, qapp: QApplication) -> None:
        view = ShoppingListView()
        sl = ShoppingList()
        view.set_shopping_list(sl)
        assert view._table.rowCount() == 0
        assert "0.00" in view._total_label.text()


class TestShoppingListViewSelectedProduct:
    def test_no_selection_returns_none(self, qapp: QApplication) -> None:
        view = ShoppingListView()
        assert view._selected_product_id() is None

    def test_selected_category_header_returns_none(self, qapp: QApplication) -> None:
        view = ShoppingListView()
        sl = _shopping_list()
        view.set_shopping_list(sl)
        view._table.setCurrentCell(0, 0)  # category header
        assert view._selected_product_id() is None

    def test_selected_data_row_returns_product_id(self, qapp: QApplication) -> None:
        view = ShoppingListView()
        sl = _shopping_list()
        view.set_shopping_list(sl)
        view._table.setCurrentCell(1, 1)  # data row
        assert view._selected_product_id() == 1
