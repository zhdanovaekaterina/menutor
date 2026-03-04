from typing import cast

from src.application.use_cases.manage_product import (
    CreateProduct,
    DeleteProduct,
    EditProduct,
    ListProducts,
    ProductData,
)
from src.domain.value_objects.types import ProductId
from src.presentation.views.product_list_view import ProductListView


class ProductController:
    """Соединяет ProductListView с use cases слоя Application."""

    def __init__(
        self,
        view: ProductListView,
        create_uc: CreateProduct,
        edit_uc: EditProduct,
        delete_uc: DeleteProduct,
        list_uc: ListProducts,
    ) -> None:
        self._view = view
        self._create_uc = create_uc
        self._edit_uc = edit_uc
        self._delete_uc = delete_uc
        self._list_uc = list_uc

        view.create_product_requested.connect(self._on_create)
        view.edit_product_requested.connect(self._on_edit)
        view.delete_product_requested.connect(self._on_delete)

        self._refresh()

    def refresh(self) -> None:
        self._refresh()

    def _refresh(self) -> None:
        try:
            products = self._list_uc.execute()
            self._view.set_products(products)
        except Exception as exc:
            self._view.show_error(str(exc))

    def _on_create(self, data: ProductData) -> None:
        try:
            self._create_uc.execute(data)
            self._refresh()
        except Exception as exc:
            self._view.show_error(str(exc))

    def _on_edit(self, product_id: object, data: ProductData) -> None:
        try:
            self._edit_uc.execute(ProductId(cast(int, product_id)), data)
            self._refresh()
        except Exception as exc:
            self._view.show_error(str(exc))

    def _on_delete(self, product_id: object) -> None:
        try:
            self._delete_uc.execute(ProductId(cast(int, product_id)))
            self._refresh()
        except Exception as exc:
            self._view.show_error(str(exc))
