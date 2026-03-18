"""Wire product use cases."""

from typing import Any

from backend.application.use_cases.manage_product import (
    CreateProduct,
    DeleteProduct,
    EditProduct,
    ListProductCategories,
    ListProducts,
    UpdateProductPrice,
)
from backend.composition._infrastructure import _Infrastructure


def _wire_products(infra: _Infrastructure) -> dict[str, Any]:
    return {
        "create_product": CreateProduct(infra.product_repo),
        "edit_product": EditProduct(infra.product_repo),
        "delete_product": DeleteProduct(infra.product_repo),
        "update_product_price": UpdateProductPrice(infra.product_repo),
        "list_products": ListProducts(infra.product_repo),
        "list_product_categories": ListProductCategories(infra.product_category_repo),
    }
