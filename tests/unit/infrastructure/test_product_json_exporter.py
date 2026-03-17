import json
from decimal import Decimal

from backend.domain.entities.product import Product
from backend.domain.value_objects.money import Money
from backend.domain.value_objects.types import ProductCategoryId, ProductId, UserId
from backend.infrastructure.export.product_json_exporter import ProductJsonExporter


def _product(id: int = 1, name: str = "Мука") -> Product:
    return Product(
        id=ProductId(id),
        name=name,
        recipe_unit="g",
        purchase_unit="kg",
        price_per_purchase_unit=Money(Decimal("60.00")),
        brand="Брэнд",
        supplier="Поставщик",
        conversion_factor=1000.0,
        category_id=ProductCategoryId(1),
        user_id=UserId(1),
    )


def test_export_bytes_returns_list() -> None:
    data = json.loads(ProductJsonExporter().export_bytes([_product()]))
    assert isinstance(data, list)
    assert len(data) == 1


def test_export_bytes_fields() -> None:
    item = json.loads(ProductJsonExporter().export_bytes([_product()]))[0]
    assert item["id"] == 1
    assert item["name"] == "Мука"
    assert item["recipe_unit"] == "g"
    assert item["purchase_unit"] == "kg"
    assert item["price_amount"] == "60.00"
    assert item["price_currency"] == "RUB"
    assert item["brand"] == "Брэнд"
    assert item["conversion_factor"] == 1000.0


def test_export_bytes_empty() -> None:
    data = json.loads(ProductJsonExporter().export_bytes([]))
    assert data == []


def test_example_bytes_is_parseable() -> None:
    data = json.loads(ProductJsonExporter().example_bytes())
    assert len(data) == 2
    assert data[0]["name"] == "Мука"
    assert data[1]["name"] == "Молоко"


def test_content_type() -> None:
    assert ProductJsonExporter().content_type() == "application/json"


def test_file_extension() -> None:
    assert ProductJsonExporter().file_extension() == "json"
