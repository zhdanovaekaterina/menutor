from decimal import Decimal

import pytest

from backend.domain.entities.product import Product
from backend.domain.value_objects.money import Money
from backend.domain.value_objects.types import ProductCategoryId, ProductId, UserId
from backend.infrastructure.repositories.sqlite_product_repository import (
    SqliteProductRepository,
)


@pytest.fixture
def repo(conn: object) -> SqliteProductRepository:
    return SqliteProductRepository(conn)  # type: ignore[arg-type]


def _flour(user_id: UserId, **kw: object) -> Product:
    defaults: dict = dict(
        id=ProductId(0), name="Мука",
        recipe_unit="g", purchase_unit="kg",
        price_per_purchase_unit=Money(Decimal("80")),
        conversion_factor=1000,
        category_id=ProductCategoryId(1),  # Сыпучие
        user_id=user_id,
    )
    defaults.update(kw)
    return Product(**defaults)


def test_save_assigns_id(repo: SqliteProductRepository, user_id: UserId) -> None:
    saved = repo.save(_flour(user_id))
    assert saved.id != ProductId(0)


def test_save_and_get_by_id_roundtrip(repo: SqliteProductRepository, user_id: UserId) -> None:
    saved = repo.save(_flour(user_id))
    retrieved = repo.get_by_id(saved.id)

    assert retrieved is not None
    assert retrieved.name == "Мука"
    assert retrieved.category_id == ProductCategoryId(1)
    assert retrieved.recipe_unit == "g"
    assert retrieved.purchase_unit == "kg"
    assert retrieved.conversion_factor == pytest.approx(1000)
    assert retrieved.price_per_purchase_unit == Money(Decimal("80"))
    assert retrieved.user_id == user_id


def test_get_by_id_returns_none_when_absent(repo: SqliteProductRepository) -> None:
    assert repo.get_by_id(ProductId(9999)) is None


def test_delete_removes_product(repo: SqliteProductRepository, user_id: UserId) -> None:
    saved = repo.save(_flour(user_id))
    repo.delete(saved.id)
    assert repo.get_by_id(saved.id) is None


def test_find_by_category_id_filters_correctly(repo: SqliteProductRepository, user_id: UserId) -> None:
    repo.save(_flour(user_id, name="Мука",   category_id=ProductCategoryId(1)))
    repo.save(_flour(user_id, name="Молоко", category_id=ProductCategoryId(2),
                     recipe_unit="ml", purchase_unit="l"))

    dry = repo.find_by_category_id(ProductCategoryId(1), user_id)
    assert len(dry) == 1
    assert dry[0].name == "Мука"


def test_find_all_returns_all_products(repo: SqliteProductRepository, user_id: UserId) -> None:
    repo.save(_flour(user_id, name="Мука"))
    repo.save(_flour(user_id, name="Молоко", category_id=ProductCategoryId(2),
                     recipe_unit="ml", purchase_unit="l"))
    assert len(repo.find_all(user_id)) == 2


def test_update_existing_product(repo: SqliteProductRepository, user_id: UserId) -> None:
    saved = repo.save(_flour(user_id))
    updated = Product(
        id=saved.id, name="Мука высш. сорт",
        recipe_unit="g", purchase_unit="kg",
        price_per_purchase_unit=Money(Decimal("120")),
        conversion_factor=1000,
        category_id=ProductCategoryId(1),
        user_id=user_id,
    )
    result = repo.save(updated)
    assert result.name == "Мука высш. сорт"
    assert result.price_per_purchase_unit == Money(Decimal("120"))


def test_brand_and_weight_per_piece_persisted(repo: SqliteProductRepository, user_id: UserId) -> None:
    saved = repo.save(_flour(user_id, brand="Аладушкин", weight_per_piece_g=1000.0))
    retrieved = repo.get_by_id(saved.id)
    assert retrieved is not None
    assert retrieved.brand == "Аладушкин"
    assert retrieved.weight_per_piece_g == pytest.approx(1000.0)
