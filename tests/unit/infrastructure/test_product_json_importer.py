import json
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from backend.domain.entities.product import Product
from backend.domain.exceptions import ImportValidationError
from backend.domain.value_objects.import_result import ImportResult
from backend.domain.value_objects.money import Money
from backend.domain.value_objects.types import ProductCategoryId, ProductId, UserId
from backend.infrastructure.import_.product_json_importer import ProductJsonImporter

UID = UserId(1)


def _make_json(*rows: dict) -> bytes:
    return json.dumps(list(rows), ensure_ascii=False).encode("utf-8")


def _row(**kwargs) -> dict:
    defaults = dict(
        name="Мука", category_id=1,
        recipe_unit="g", purchase_unit="kg",
        price_amount="60.00", price_currency="RUB",
        brand="", supplier="", conversion_factor=1000,
    )
    defaults.update(kwargs)
    return defaults


def _mock_repo(existing: Product | None = None) -> MagicMock:
    repo = MagicMock()
    repo.get_by_id.return_value = existing
    repo.save.side_effect = lambda p: p
    return repo


def test_create_new_product() -> None:
    result = ProductJsonImporter(_mock_repo()).import_from_bytes(_make_json(_row()), UID)
    assert result == ImportResult(created=1, updated=0)


def test_update_existing_product() -> None:
    existing = Product(
        id=ProductId(3), name="Мука", recipe_unit="g", purchase_unit="kg",
        price_per_purchase_unit=Money(Decimal("60")),
        category_id=ProductCategoryId(1), user_id=UID,
    )
    repo = _mock_repo(existing=existing)
    result = ProductJsonImporter(repo).import_from_bytes(_make_json(_row(id=3)), UID)
    assert result == ImportResult(created=0, updated=1)
    saved: Product = repo.save.call_args[0][0]
    assert saved.id == ProductId(3)


def test_id_belonging_to_other_user_creates_new() -> None:
    other = Product(
        id=ProductId(3), name="Мука", recipe_unit="g", purchase_unit="kg",
        price_per_purchase_unit=Money(Decimal("60")),
        category_id=ProductCategoryId(1), user_id=UserId(99),
    )
    repo = _mock_repo(existing=other)
    result = ProductJsonImporter(repo).import_from_bytes(_make_json(_row(id=3)), UID)
    assert result == ImportResult(created=1, updated=0)


def test_mixed_create_and_update() -> None:
    existing = Product(
        id=ProductId(1), name="Мука", recipe_unit="g", purchase_unit="kg",
        price_per_purchase_unit=Money(Decimal("60")),
        category_id=ProductCategoryId(1), user_id=UID,
    )
    repo = MagicMock()
    repo.get_by_id.return_value = existing
    repo.save.side_effect = lambda p: p
    result = ProductJsonImporter(repo).import_from_bytes(
        _make_json(_row(id=1), _row(name="Молоко")), UID
    )
    assert result == ImportResult(created=1, updated=1)


def test_missing_required_field_raises() -> None:
    row = _row()
    del row["name"]
    with pytest.raises(ImportValidationError, match="name"):
        ProductJsonImporter(_mock_repo()).import_from_bytes(_make_json(row), UID)


def test_empty_name_raises() -> None:
    with pytest.raises(ImportValidationError, match="name"):
        ProductJsonImporter(_mock_repo()).import_from_bytes(_make_json(_row(name="")), UID)


def test_malformed_json_raises() -> None:
    with pytest.raises(ImportValidationError, match="JSON"):
        ProductJsonImporter(_mock_repo()).import_from_bytes(b"{not valid json}", UID)


def test_json_not_array_raises() -> None:
    with pytest.raises(ImportValidationError, match="массивом"):
        ProductJsonImporter(_mock_repo()).import_from_bytes('{"name":"Мука"}'.encode("utf-8"), UID)


def test_empty_bytes_returns_zero() -> None:
    result = ProductJsonImporter(_mock_repo()).import_from_bytes(b"", UID)
    assert result == ImportResult(created=0, updated=0)


def test_supported_extensions() -> None:
    assert ProductJsonImporter(_mock_repo()).supported_extensions() == ["json"]
