from decimal import Decimal

import pytest
from sqlalchemy import text

from backend.domain.entities.product import Product
from backend.domain.exceptions import DomainError
from backend.domain.value_objects.money import Money
from backend.domain.value_objects.types import ProductCategoryId, ProductId, UserId
from backend.infrastructure.repositories.orm_product_repository import (
    OrmProductRepository,
)


@pytest.fixture
def repo(conn: object) -> OrmProductRepository:
    return OrmProductRepository(conn)  # type: ignore[arg-type]


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


def test_save_assigns_id(repo: OrmProductRepository, user_id: UserId) -> None:
    saved = repo.save(_flour(user_id))
    assert saved.id != ProductId(0)


def test_save_and_get_by_id_roundtrip(repo: OrmProductRepository, user_id: UserId) -> None:
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


def test_get_by_id_returns_none_when_absent(repo: OrmProductRepository) -> None:
    assert repo.get_by_id(ProductId(9999)) is None


def test_delete_removes_product(repo: OrmProductRepository, user_id: UserId) -> None:
    saved = repo.save(_flour(user_id))
    repo.delete([saved.id])
    assert repo.get_by_id(saved.id) is None


def test_find_by_category_id_filters_correctly(repo: OrmProductRepository, user_id: UserId) -> None:
    repo.save(_flour(user_id, name="Мука",   category_id=ProductCategoryId(1)))
    repo.save(_flour(user_id, name="Молоко", category_id=ProductCategoryId(2),
                     recipe_unit="ml", purchase_unit="l"))

    dry = repo.find_by_category_id(ProductCategoryId(1), user_id)
    assert len(dry) == 1
    assert dry[0].name == "Мука"


def test_find_all_returns_all_products(repo: OrmProductRepository, user_id: UserId) -> None:
    repo.save(_flour(user_id, name="Мука"))
    repo.save(_flour(user_id, name="Молоко", category_id=ProductCategoryId(2),
                     recipe_unit="ml", purchase_unit="l"))
    assert len(repo.find_all(user_id)) == 2


def test_update_existing_product(repo: OrmProductRepository, user_id: UserId) -> None:
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


def test_brand_persisted(repo: OrmProductRepository, user_id: UserId) -> None:
    saved = repo.save(_flour(user_id, brand="Аладушкин"))
    retrieved = repo.get_by_id(saved.id)
    assert retrieved is not None
    assert retrieved.brand == "Аладушкин"


def test_delete_rejects_linked_products(
    repo: OrmProductRepository, conn: object, user_id: UserId
) -> None:
    """Deleting a product used in a recipe must raise DomainError
    and leave all products intact."""
    from sqlalchemy.orm import Session
    session: Session = conn  # type: ignore[assignment]

    p1 = repo.save(_flour(user_id, name="Мука"))
    p2 = repo.save(_flour(user_id, name="Сахар"))

    # Create a recipe that uses p1
    recipe_cat_id = session.execute(
        text("SELECT id FROM recipe_categories LIMIT 1")
    ).scalar()
    session.execute(
        text("INSERT INTO recipes (id, name, category_id, servings, user_id) "
             "VALUES (9000, 'Тест', :cat, 1, :uid)"),
        {"cat": recipe_cat_id, "uid": int(user_id)},
    )
    session.execute(
        text("INSERT INTO recipe_ingredients (recipe_id, product_id, amount, unit) "
             "VALUES (9000, :pid, 100, 'g')"),
        {"pid": int(p1.id)},
    )
    session.commit()

    with pytest.raises(DomainError, match="Мука"):
        repo.delete([p1.id, p2.id])

    # Both products must still exist
    assert repo.get_by_id(p1.id) is not None
    assert repo.get_by_id(p2.id) is not None


def test_find_linked_ids(
    repo: OrmProductRepository, conn: object, user_id: UserId
) -> None:
    from sqlalchemy.orm import Session
    session: Session = conn  # type: ignore[assignment]

    p1 = repo.save(_flour(user_id, name="Мука"))
    p2 = repo.save(_flour(user_id, name="Сахар"))

    recipe_cat_id = session.execute(
        text("SELECT id FROM recipe_categories LIMIT 1")
    ).scalar()
    session.execute(
        text("INSERT INTO recipes (id, name, category_id, servings, user_id) "
             "VALUES (9001, 'Тест', :cat, 1, :uid)"),
        {"cat": recipe_cat_id, "uid": int(user_id)},
    )
    session.execute(
        text("INSERT INTO recipe_ingredients (recipe_id, product_id, amount, unit) "
             "VALUES (9001, :pid, 100, 'g')"),
        {"pid": int(p1.id)},
    )
    session.commit()

    linked = repo.find_linked_ids([p1.id, p2.id])
    assert linked == [p1.id]
