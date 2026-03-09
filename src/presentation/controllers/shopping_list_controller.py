import logging

from src.application.use_cases.import_export import (
    ExportShoppingListAsCsv,
    ExportShoppingListAsText,
)
from src.application.use_cases.manage_product import ListProductCategories, ListProducts
from src.domain.entities.shopping_list import ShoppingList, ShoppingListItem
from src.domain.exceptions import AppError
from src.domain.value_objects.quantity import Quantity
from src.domain.value_objects.types import ProductId
from src.presentation.views.shopping_list_view import ShoppingListView

logger = logging.getLogger(__name__)


class ShoppingListController:
    """Соединяет ShoppingListView с use cases экспорта."""

    def __init__(
        self,
        view: ShoppingListView,
        export_text_uc: ExportShoppingListAsText,
        export_csv_uc: ExportShoppingListAsCsv,
        list_products_uc: ListProducts,
        list_product_categories_uc: ListProductCategories,
    ) -> None:
        self._view = view
        self._export_text_uc = export_text_uc
        self._export_csv_uc = export_csv_uc
        self._list_products_uc = list_products_uc
        self._list_product_categories_uc = list_product_categories_uc
        self._shopping_list: ShoppingList | None = None

        view.export_text_requested.connect(self._on_export_text)
        view.export_csv_requested.connect(self._on_export_csv)
        view.add_product_requested.connect(self._on_add_product)
        view.quantity_edited.connect(self._on_quantity_edited)
        view.remove_product_requested.connect(self._on_remove_product)

        self._refresh_products()

    def refresh(self) -> None:
        self._refresh_products()

    def _refresh_products(self) -> None:
        try:
            products = self._list_products_uc.execute()
            self._view.set_products(products)
        except AppError as exc:
            logger.warning("Ошибка при загрузке продуктов: %s", exc)
            self._view.show_error(str(exc))

    def set_shopping_list(self, shopping_list: ShoppingList) -> None:
        self._shopping_list = shopping_list
        self._view.set_shopping_list(shopping_list)

    def _on_export_text(self) -> None:
        if self._shopping_list is None:
            return
        try:
            text = self._export_text_uc.execute(self._shopping_list)
            self._view.show_text_export(text)
        except AppError as exc:
            logger.warning("Ошибка при экспорте текста: %s", exc)
            self._view.show_error(str(exc))

    def _on_export_csv(self, filepath: str) -> None:
        if self._shopping_list is None:
            return
        try:
            self._export_csv_uc.execute(self._shopping_list, filepath)
        except AppError as exc:
            logger.warning("Ошибка при экспорте CSV: %s", exc)
            self._view.show_error(str(exc))

    def _on_add_product(self, product_id: int, qty_in_recipe_unit: float) -> None:
        if self._shopping_list is None:
            return
        try:
            products = self._list_products_uc.execute()
            product = next((p for p in products if p.id == ProductId(product_id)), None)
            if product is None:
                self._view.show_error("Продукт не найден.")
                return

            category_map = dict(self._list_product_categories_uc.execute())

            purchase_qty, cost = product.compute_purchase(qty_in_recipe_unit)

            item = ShoppingListItem(
                product_id=ProductId(product_id),
                product_name=product.name,
                category=category_map.get(product.category_id, ""),
                quantity=purchase_qty,
                cost=cost,
            )
            self._shopping_list.items.append(item)
            self._view.set_shopping_list(self._shopping_list)
        except AppError as exc:
            logger.warning("Ошибка при добавлении продукта %s: %s", product_id, exc)
            self._view.show_error(str(exc))

    def _on_remove_product(self, product_id: int) -> None:
        if self._shopping_list is None:
            return
        pid = ProductId(product_id)
        self._shopping_list.items = [
            i for i in self._shopping_list.items if i.product_id != pid
        ]
        self._view.set_shopping_list(self._shopping_list)

    def _on_quantity_edited(self, product_id: int, new_purchase_qty: float) -> None:
        if self._shopping_list is None:
            return
        try:
            pid = ProductId(product_id)
            item = next((i for i in self._shopping_list.items if i.product_id == pid), None)
            if item is None:
                return

            products = self._list_products_uc.execute()
            product = next((p for p in products if p.id == pid), None)
            if product is None:
                return

            item.quantity = Quantity(new_purchase_qty, item.quantity.unit)
            item.cost = product.purchase_cost(new_purchase_qty)
            self._view.set_shopping_list(self._shopping_list)
        except AppError as exc:
            logger.warning("Ошибка при изменении количества: %s", exc)
            self._view.show_error(str(exc))
