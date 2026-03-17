from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from backend.application.use_cases.export_entities import ExportEntities
from backend.domain.entities.product import Product
from backend.domain.exceptions import ImportValidationError
from backend.domain.value_objects.money import Money
from backend.domain.value_objects.types import ProductCategoryId, ProductId, UserId
from backend.infrastructure.export.registry import ExportRegistry

UID = UserId(1)


def _make_exporter(ext: str = "csv", ct: str = "text/csv") -> MagicMock:
    exporter = MagicMock()
    exporter.export_bytes.return_value = b"data"
    exporter.example_bytes.return_value = b"example"
    exporter.content_type.return_value = ct
    exporter.file_extension.return_value = ext
    return exporter


def _product(id: int = 1) -> Product:
    return Product(
        id=ProductId(id),
        name="Мука",
        recipe_unit="g",
        purchase_unit="kg",
        price_per_purchase_unit=Money(Decimal("60")),
        category_id=ProductCategoryId(1),
        user_id=UID,
    )


def _make_use_case(
    exporter: MagicMock | None = None,
    products: list | None = None,
    recipes: list | None = None,
    menus: list | None = None,
) -> ExportEntities:
    registry = ExportRegistry()
    if exporter:
        registry.register("products", "csv", exporter)
        registry.register("recipes", "csv", exporter)
        registry.register("menus", "json", exporter)

    product_repo = MagicMock()
    product_repo.find_all.return_value = products or []
    recipe_repo = MagicMock()
    recipe_repo.find_all.return_value = recipes or []
    menu_repo = MagicMock()
    menu_repo.find_all.return_value = menus or []

    return ExportEntities(registry, product_repo, recipe_repo, menu_repo)


def test_execute_returns_bytes_content_type_filename() -> None:
    exporter = _make_exporter()
    uc = _make_use_case(exporter=exporter, products=[_product()])
    data, ct, filename = uc.execute("products", "csv", UID)
    assert data == b"data"
    assert ct == "text/csv"
    assert filename == "products.csv"


def test_execute_passes_entities_to_exporter() -> None:
    exporter = _make_exporter()
    p = _product()
    uc = _make_use_case(exporter=exporter, products=[p])
    uc.execute("products", "csv", UID)
    exporter.export_bytes.assert_called_once_with([p])


def test_execute_filters_by_entity_ids() -> None:
    exporter = _make_exporter()
    p1, p2, p3 = _product(1), _product(2), _product(3)
    uc = _make_use_case(exporter=exporter, products=[p1, p2, p3])
    uc.execute("products", "csv", UID, entity_ids=[1, 3])
    called_with = exporter.export_bytes.call_args[0][0]
    assert len(called_with) == 2
    assert p2 not in called_with


def test_execute_all_when_no_ids_filter() -> None:
    exporter = _make_exporter()
    p1, p2 = _product(1), _product(2)
    uc = _make_use_case(exporter=exporter, products=[p1, p2])
    uc.execute("products", "csv", UID)
    called_with = exporter.export_bytes.call_args[0][0]
    assert len(called_with) == 2


def test_execute_unknown_format_raises() -> None:
    uc = _make_use_case()
    with pytest.raises(ImportValidationError, match="xml"):
        uc.execute("products", "xml", UID)


def test_execute_unknown_entity_type_raises() -> None:
    uc = _make_use_case()
    with pytest.raises(ImportValidationError):
        uc.execute("unknown", "csv", UID)


def test_example_returns_bytes_content_type_filename() -> None:
    exporter = _make_exporter()
    uc = _make_use_case(exporter=exporter)
    data, ct, filename = uc.example("products", "csv")
    assert data == b"example"
    assert "example_" in filename


def test_example_unknown_format_raises() -> None:
    uc = _make_use_case()
    with pytest.raises(ImportValidationError):
        uc.example("products", "xml")
