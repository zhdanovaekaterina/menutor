import csv
import io
from decimal import Decimal

from backend.domain.entities.product import Product
from backend.domain.value_objects.money import Money
from backend.domain.value_objects.types import ProductCategoryId, ProductId, UserId
from backend.infrastructure.export.product_csv_exporter import ProductCsvExporter


def _product(
    id: int = 1,
    name: str = "Мука",
    category_id: int = 1,
    recipe_unit: str = "g",
    purchase_unit: str = "kg",
    price: str = "60.00",
    brand: str = "",
    supplier: str = "",
    conversion_factor: float = 1000.0,
) -> Product:
    return Product(
        id=ProductId(id),
        name=name,
        recipe_unit=recipe_unit,
        purchase_unit=purchase_unit,
        price_per_purchase_unit=Money(Decimal(price)),
        brand=brand,
        supplier=supplier,
        conversion_factor=conversion_factor,
        category_id=ProductCategoryId(category_id),
        user_id=UserId(1),
    )


def _parse_csv(data: bytes) -> list[list[str]]:
    return list(csv.reader(io.StringIO(data.decode("utf-8"))))


def test_export_bytes_header() -> None:
    rows = _parse_csv(ProductCsvExporter().export_bytes([]))
    assert rows[0] == [
        "id", "name", "category_id", "recipe_unit", "purchase_unit",
        "price_amount", "price_currency", "brand", "supplier", "conversion_factor",
    ]


def test_export_bytes_single_product() -> None:
    rows = _parse_csv(ProductCsvExporter().export_bytes([_product()]))
    assert len(rows) == 2
    assert rows[1][0] == "1"
    assert rows[1][1] == "Мука"
    assert rows[1][5] == "60.00"
    assert rows[1][6] == "RUB"
    assert rows[1][9] == "1000.0"


def test_export_bytes_two_products() -> None:
    rows = _parse_csv(ProductCsvExporter().export_bytes([_product(1), _product(2, name="Молоко")]))
    assert len(rows) == 3


def test_export_bytes_empty() -> None:
    rows = _parse_csv(ProductCsvExporter().export_bytes([]))
    assert len(rows) == 1  # header only


def test_example_bytes_is_parseable() -> None:
    rows = _parse_csv(ProductCsvExporter().example_bytes())
    assert len(rows) == 3  # header + 2 example rows
    assert rows[1][1] == "Мука"
    assert rows[2][1] == "Молоко"


def test_content_type() -> None:
    assert ProductCsvExporter().content_type() == "text/csv; charset=utf-8"


def test_file_extension() -> None:
    assert ProductCsvExporter().file_extension() == "csv"
