import json
from typing import Any

from backend.domain.entities.product import Product


class ProductJsonExporter:
    """Exports Product entities to JSON bytes."""

    def _to_dict(self, product: Product) -> dict[str, Any]:
        return {
            "id": product.id,
            "name": product.name,
            "category_id": product.category_id,
            "recipe_unit": product.recipe_unit,
            "purchase_unit": product.purchase_unit,
            "price_amount": str(product.price_per_purchase_unit.amount),
            "price_currency": product.price_per_purchase_unit.currency,
            "brand": product.brand,
            "supplier": product.supplier,
            "conversion_factor": product.conversion_factor,
        }

    def export_bytes(self, entities: list[Any]) -> bytes:
        data = [self._to_dict(p) for p in entities]
        return json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")

    def example_bytes(self) -> bytes:
        examples = [
            {
                "id": 1, "name": "Мука", "category_id": 1,
                "recipe_unit": "g", "purchase_unit": "kg",
                "price_amount": "60.00", "price_currency": "RUB",
                "brand": "", "supplier": "", "conversion_factor": 1000,
            },
            {
                "id": 2, "name": "Молоко", "category_id": 2,
                "recipe_unit": "ml", "purchase_unit": "l",
                "price_amount": "80.00", "price_currency": "RUB",
                "brand": "", "supplier": "", "conversion_factor": 1000,
            },
        ]
        return json.dumps(examples, ensure_ascii=False, indent=2).encode("utf-8")

    def content_type(self) -> str:
        return "application/json"

    def file_extension(self) -> str:
        return "json"
