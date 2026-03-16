import csv
import io
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from backend.domain.entities.product import Product
from backend.domain.exceptions import ImportValidationError
from backend.domain.value_objects.import_result import ImportResult
from backend.domain.value_objects.money import Money
from backend.domain.value_objects.types import ProductCategoryId, ProductId, UserId
from backend.infrastructure.import_.product_csv_importer import ProductCsvImporter

UID = UserId(1)


def _make_csv(*rows: dict) -> bytes:
    if not rows:
        return b""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue().encode("utf-8")


def _row(**kwargs) -> dict:
    defaults = dict(
        id="", name="Мука", category_id="1",
        recipe_unit="g", purchase_unit="kg",
        price_amount="60.00", price_currency="RUB",
        brand="", supplier="", conversion_factor="1000",
    )
    defaults.update(kwargs)
    return defaults


def _mock_repo(existing: Product | None = None) -> MagicMock:
    repo = MagicMock()
    repo.get_by_id.return_value = existing
    repo.save.side_effect = lambda p: p
    return repo


def test_create_new_product() -> None:
    repo = _mock_repo()
    result = ProductCsvImporter(repo).import_from_bytes(_make_csv(_row()), UID)
    assert result == ImportResult(created=1, updated=0)
    repo.save.assert_called_once()
    saved: Product = repo.save.call_args[0][0]
    assert saved.id == ProductId(0)
    assert saved.name == "Мука"
    assert saved.user_id == UID


def test_update_existing_product() -> None:
    existing = Product(
        id=ProductId(5), name="Мука", recipe_unit="g", purchase_unit="kg",
        price_per_purchase_unit=Money(Decimal("60")),
        category_id=ProductCategoryId(1), user_id=UID,
    )
    repo = _mock_repo(existing=existing)
    result = ProductCsvImporter(repo).import_from_bytes(_make_csv(_row(id="5")), UID)
    assert result == ImportResult(created=0, updated=1)
    saved: Product = repo.save.call_args[0][0]
    assert saved.id == ProductId(5)


def test_id_belonging_to_other_user_creates_new() -> None:
    other_user_product = Product(
        id=ProductId(5), name="Мука", recipe_unit="g", purchase_unit="kg",
        price_per_purchase_unit=Money(Decimal("60")),
        category_id=ProductCategoryId(1), user_id=UserId(99),
    )
    repo = _mock_repo(existing=other_user_product)
    result = ProductCsvImporter(repo).import_from_bytes(_make_csv(_row(id="5")), UID)
    assert result == ImportResult(created=1, updated=0)
    saved: Product = repo.save.call_args[0][0]
    assert saved.id == ProductId(0)


def test_mixed_create_and_update() -> None:
    existing = Product(
        id=ProductId(1), name="Мука", recipe_unit="g", purchase_unit="kg",
        price_per_purchase_unit=Money(Decimal("60")),
        category_id=ProductCategoryId(1), user_id=UID,
    )
    repo = MagicMock()
    repo.get_by_id.return_value = existing
    repo.save.side_effect = lambda p: p
    result = ProductCsvImporter(repo).import_from_bytes(
        _make_csv(_row(id="1"), _row(name="Молоко")), UID
    )
    assert result == ImportResult(created=1, updated=1)


def test_missing_required_field_raises() -> None:
    row = _row()
    del row["name"]
    with pytest.raises(ImportValidationError, match="name"):
        ProductCsvImporter(_mock_repo()).import_from_bytes(_make_csv(row), UID)


def test_empty_name_raises() -> None:
    with pytest.raises(ImportValidationError, match="name"):
        ProductCsvImporter(_mock_repo()).import_from_bytes(_make_csv(_row(name="")), UID)


def test_invalid_price_raises() -> None:
    with pytest.raises(ImportValidationError, match="price_amount"):
        ProductCsvImporter(_mock_repo()).import_from_bytes(_make_csv(_row(price_amount="abc")), UID)


def test_empty_bytes_returns_zero() -> None:
    result = ProductCsvImporter(_mock_repo()).import_from_bytes(b"", UID)
    assert result == ImportResult(created=0, updated=0)


def test_supported_extensions() -> None:
    assert ProductCsvImporter(_mock_repo()).supported_extensions() == ["csv"]
