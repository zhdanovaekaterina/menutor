"""Unit tests for ShoppingListController — verifies export, add/remove/edit product logic."""

from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from src.domain.entities.product import Product
from src.domain.entities.shopping_list import ShoppingList, ShoppingListItem
from src.domain.value_objects.money import Money
from src.domain.value_objects.quantity import Quantity
from src.domain.value_objects.types import ProductCategoryId, ProductId
from src.presentation.controllers.shopping_list_controller import ShoppingListController


@pytest.fixture
def view() -> MagicMock:
    return MagicMock()


@pytest.fixture
def export_text_uc() -> MagicMock:
    return MagicMock()


@pytest.fixture
def export_csv_uc() -> MagicMock:
    return MagicMock()


@pytest.fixture
def list_products_uc() -> MagicMock:
    return MagicMock()


@pytest.fixture
def list_product_categories_uc() -> MagicMock:
    return MagicMock()


@pytest.fixture
def sample_products() -> list[Product]:
    return [
        Product(
            id=ProductId(1), name="Мука",
            recipe_unit="g", purchase_unit="kg",
            price_per_purchase_unit=Money(Decimal("80")),
            conversion_factor=0.001,
            category_id=ProductCategoryId(1),
        ),
        Product(
            id=ProductId(2), name="Молоко",
            recipe_unit="ml", purchase_unit="l",
            price_per_purchase_unit=Money(Decimal("90")),
            conversion_factor=0.001,
            category_id=ProductCategoryId(2),
        ),
    ]


@pytest.fixture
def sample_shopping_list() -> ShoppingList:
    return ShoppingList(items=[
        ShoppingListItem(
            product_id=ProductId(1),
            product_name="Мука",
            category="Бакалея",
            quantity=Quantity(0.5, "kg"),
            cost=Money(Decimal("40")),
        ),
    ])


@pytest.fixture
def controller(
    view: MagicMock,
    export_text_uc: MagicMock,
    export_csv_uc: MagicMock,
    list_products_uc: MagicMock,
    list_product_categories_uc: MagicMock,
    sample_products: list[Product],
) -> ShoppingListController:
    list_products_uc.execute.return_value = sample_products
    list_product_categories_uc.execute.return_value = [(1, "Бакалея"), (2, "Молочные")]
    return ShoppingListController(
        view, export_text_uc, export_csv_uc, list_products_uc, list_product_categories_uc,
    )


class TestShoppingListControllerExport:
    def test_export_text_does_nothing_without_shopping_list(
        self, export_text_uc: MagicMock, controller: ShoppingListController,
    ) -> None:
        controller._on_export_text()
        export_text_uc.execute.assert_not_called()

    def test_export_text_delegates_to_use_case(
        self,
        export_text_uc: MagicMock,
        view: MagicMock,
        sample_shopping_list: ShoppingList,
        controller: ShoppingListController,
    ) -> None:
        controller.set_shopping_list(sample_shopping_list)
        export_text_uc.execute.return_value = "Мука: 0.5 kg"
        controller._on_export_text()
        export_text_uc.execute.assert_called_once_with(sample_shopping_list)
        view.show_text_export.assert_called_once_with("Мука: 0.5 kg")

    def test_export_csv_does_nothing_without_shopping_list(
        self, export_csv_uc: MagicMock, controller: ShoppingListController,
    ) -> None:
        controller._on_export_csv("/tmp/test.csv")
        export_csv_uc.execute.assert_not_called()

    def test_export_csv_delegates_to_use_case(
        self,
        export_csv_uc: MagicMock,
        sample_shopping_list: ShoppingList,
        controller: ShoppingListController,
    ) -> None:
        controller.set_shopping_list(sample_shopping_list)
        controller._on_export_csv("/tmp/test.csv")
        export_csv_uc.execute.assert_called_once_with(sample_shopping_list, "/tmp/test.csv")

    def test_export_text_shows_error_on_failure(
        self,
        export_text_uc: MagicMock,
        view: MagicMock,
        sample_shopping_list: ShoppingList,
        controller: ShoppingListController,
    ) -> None:
        controller.set_shopping_list(sample_shopping_list)
        export_text_uc.execute.side_effect = RuntimeError("Exporter failed")
        controller._on_export_text()
        view.show_error.assert_called_once_with("Exporter failed")


class TestShoppingListControllerSetShoppingList:
    def test_set_shopping_list_updates_view(
        self,
        view: MagicMock,
        sample_shopping_list: ShoppingList,
        controller: ShoppingListController,
    ) -> None:
        controller.set_shopping_list(sample_shopping_list)
        view.set_shopping_list.assert_called_once_with(sample_shopping_list)


class TestShoppingListControllerAddProduct:
    def test_add_product_creates_item_and_updates_list(
        self,
        view: MagicMock,
        sample_shopping_list: ShoppingList,
        controller: ShoppingListController,
    ) -> None:
        controller.set_shopping_list(sample_shopping_list)
        view.set_shopping_list.reset_mock()

        # Add 500ml of milk (product_id=2, conversion_factor=0.001)
        controller._on_add_product(2, 500.0)

        assert len(sample_shopping_list.items) == 2
        added_item = sample_shopping_list.items[1]
        assert added_item.product_id == ProductId(2)
        assert added_item.product_name == "Молоко"
        assert added_item.quantity.unit == "l"
        assert added_item.quantity.amount == pytest.approx(0.5)
        view.set_shopping_list.assert_called_once()

    def test_add_product_not_found_shows_error(
        self,
        view: MagicMock,
        sample_shopping_list: ShoppingList,
        controller: ShoppingListController,
    ) -> None:
        controller.set_shopping_list(sample_shopping_list)
        controller._on_add_product(999, 100.0)
        view.show_error.assert_called_once_with("Продукт не найден.")

    def test_add_product_does_nothing_without_shopping_list(
        self, view: MagicMock, controller: ShoppingListController,
    ) -> None:
        view.set_shopping_list.reset_mock()
        controller._on_add_product(1, 100.0)
        view.set_shopping_list.assert_not_called()


class TestShoppingListControllerRemoveProduct:
    def test_remove_product_filters_item(
        self,
        view: MagicMock,
        sample_shopping_list: ShoppingList,
        controller: ShoppingListController,
    ) -> None:
        controller.set_shopping_list(sample_shopping_list)
        view.set_shopping_list.reset_mock()
        controller._on_remove_product(1)
        assert len(sample_shopping_list.items) == 0
        view.set_shopping_list.assert_called_once()

    def test_remove_nonexistent_product_keeps_list(
        self,
        view: MagicMock,
        sample_shopping_list: ShoppingList,
        controller: ShoppingListController,
    ) -> None:
        controller.set_shopping_list(sample_shopping_list)
        controller._on_remove_product(999)
        assert len(sample_shopping_list.items) == 1


class TestShoppingListControllerQuantityEdited:
    def test_quantity_edited_updates_item(
        self,
        view: MagicMock,
        sample_shopping_list: ShoppingList,
        controller: ShoppingListController,
    ) -> None:
        controller.set_shopping_list(sample_shopping_list)
        view.set_shopping_list.reset_mock()
        controller._on_quantity_edited(1, 1.0)

        item = sample_shopping_list.items[0]
        assert item.quantity.amount == pytest.approx(1.0)
        assert item.quantity.unit == "kg"
        assert item.cost == Money(Decimal("80")) * 1.0
        view.set_shopping_list.assert_called_once()

    def test_quantity_edited_does_nothing_without_shopping_list(
        self, controller: ShoppingListController,
    ) -> None:
        # Should not raise
        controller._on_quantity_edited(1, 2.0)

    def test_quantity_edited_ignores_unknown_product(
        self,
        view: MagicMock,
        sample_shopping_list: ShoppingList,
        controller: ShoppingListController,
    ) -> None:
        controller.set_shopping_list(sample_shopping_list)
        view.set_shopping_list.reset_mock()
        controller._on_quantity_edited(999, 1.0)
        view.set_shopping_list.assert_not_called()
