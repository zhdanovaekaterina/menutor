"""Integration tests for OrmSavedShoppingListRepository."""
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from backend.domain.entities.saved_shopping_list import (
    SavedShoppingList,
    SavedShoppingListItem,
)
from backend.domain.entities.product import Product
from backend.domain.value_objects.money import Money
from backend.domain.value_objects.quantity import Quantity
from backend.domain.value_objects.types import (
    MenuId,
    ProductCategoryId,
    ProductId,
    SavedShoppingListId,
    SavedShoppingListItemId,
    UserId,
)
from backend.infrastructure.repositories.orm_product_repository import (
    OrmProductRepository,
)
from backend.infrastructure.repositories.orm_saved_shopping_list_repository import (
    OrmSavedShoppingListRepository,
)


@pytest.fixture
def repo(conn: object) -> OrmSavedShoppingListRepository:
    return OrmSavedShoppingListRepository(conn)  # type: ignore[arg-type]


@pytest.fixture
def seeded_product(conn: object, user_id: UserId) -> Product:
    product_repo = OrmProductRepository(conn)  # type: ignore[arg-type]
    return product_repo.save(
        Product(
            id=ProductId(0),
            name="Мука",
            recipe_unit="g",
            purchase_unit="kg",
            price_per_purchase_unit=Money(Decimal("80")),
            conversion_factor=1000,
            category_id=ProductCategoryId(1),
            user_id=user_id,
        )
    )


def _make_item(
    product_id: ProductId | None = None,
    product_name: str = "Мука",
    category: str = "Сыпучие",
    quantity: Quantity | None = None,
    buy_quantity: Quantity | None = None,
    cost: Money | None = None,
    purchased: bool = False,
    item_order: int = 0,
    recipe_quantity: Quantity | None = None,
    buy_quantity_overridden: bool = False,
) -> SavedShoppingListItem:
    return SavedShoppingListItem(
        id=SavedShoppingListItemId(0),
        product_id=product_id,
        product_name=product_name,
        category=category,
        quantity=quantity or Quantity(500.0, "g"),
        buy_quantity=buy_quantity or Quantity(1.0, "kg"),
        buy_quantity_overridden=buy_quantity_overridden,
        recipe_quantity=recipe_quantity,
        cost=cost or Money(Decimal("40")),
        purchased=purchased,
        item_order=item_order,
    )


def _make_list(
    user_id: UserId,
    name: str = "Тестовый список",
    items: list[SavedShoppingListItem] | None = None,
    source_menu_id: MenuId | None = None,
    created_at: datetime | None = None,
) -> SavedShoppingList:
    now = created_at or datetime.now(UTC)
    return SavedShoppingList(
        id=SavedShoppingListId(0),
        user_id=user_id,
        name=name,
        items=items or [],
        source_menu_id=source_menu_id,
        created_at=now,
        updated_at=now,
    )


# ---------------------------------------------------------------------------
# save (create)
# ---------------------------------------------------------------------------


def test_save_new_list_assigns_id(
    repo: OrmSavedShoppingListRepository, user_id: UserId
) -> None:
    saved = repo.save(_make_list(user_id))
    assert saved.id != SavedShoppingListId(0)


def test_save_new_list_with_items_persists_items(
    repo: OrmSavedShoppingListRepository,
    user_id: UserId,
    seeded_product: Product,
) -> None:
    item = _make_item(product_id=seeded_product.id, product_name="Мука", item_order=0)
    saved = repo.save(_make_list(user_id, items=[item]))

    assert len(saved.items) == 1
    assert saved.items[0].product_name == "Мука"
    assert saved.items[0].product_id == seeded_product.id


def test_save_new_list_stores_all_fields(
    repo: OrmSavedShoppingListRepository, user_id: UserId
) -> None:
    created_at = datetime(2026, 3, 21, 10, 0, 0, tzinfo=UTC)
    shopping_list = SavedShoppingList(
        id=SavedShoppingListId(0),
        user_id=user_id,
        name="Покупки на неделю",
        items=[],
        source_menu_id=None,
        created_at=created_at,
        updated_at=created_at,
    )
    saved = repo.save(shopping_list)

    retrieved = repo.get_by_id(saved.id)
    assert retrieved is not None
    assert retrieved.name == "Покупки на неделю"
    assert retrieved.user_id == user_id
    assert retrieved.source_menu_id is None


def test_save_new_list_with_product_id_none(
    repo: OrmSavedShoppingListRepository, user_id: UserId
) -> None:
    """Items with product_id=None (deleted product) are saved correctly."""
    item = _make_item(product_id=None, product_name="Удалённый продукт")
    saved = repo.save(_make_list(user_id, items=[item]))

    retrieved = repo.get_by_id(saved.id)
    assert retrieved is not None
    assert len(retrieved.items) == 1
    assert retrieved.items[0].product_id is None
    assert retrieved.items[0].product_name == "Удалённый продукт"


# ---------------------------------------------------------------------------
# save (update)
# ---------------------------------------------------------------------------


def test_save_update_replaces_items(
    repo: OrmSavedShoppingListRepository,
    user_id: UserId,
    seeded_product: Product,
) -> None:
    item_a = _make_item(product_name="Мука", item_order=0)
    original = repo.save(_make_list(user_id, items=[item_a]))

    item_b = _make_item(product_name="Сахар", item_order=0)
    updated_entity = SavedShoppingList(
        id=original.id,
        user_id=user_id,
        name="Обновлённый список",
        items=[item_b],
        source_menu_id=None,
        created_at=original.created_at,
        updated_at=datetime.now(UTC),
    )
    updated = repo.save(updated_entity)

    assert updated.name == "Обновлённый список"
    assert len(updated.items) == 1
    assert updated.items[0].product_name == "Сахар"


def test_save_update_preserves_created_at(
    repo: OrmSavedShoppingListRepository, user_id: UserId
) -> None:
    created_at = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
    original = repo.save(_make_list(user_id, created_at=created_at))

    updated_entity = SavedShoppingList(
        id=original.id,
        user_id=user_id,
        name="Переименованный",
        items=[],
        source_menu_id=None,
        created_at=original.created_at,
        updated_at=datetime.now(UTC),
    )
    updated = repo.save(updated_entity)

    retrieved = repo.get_by_id(updated.id)
    assert retrieved is not None
    # created_at must not change on update
    assert retrieved.created_at == original.created_at


# ---------------------------------------------------------------------------
# get_by_id
# ---------------------------------------------------------------------------


def test_get_by_id_returns_list_with_items(
    repo: OrmSavedShoppingListRepository, user_id: UserId
) -> None:
    item = _make_item(product_name="Яйца", category="Молочные", item_order=0)
    saved = repo.save(_make_list(user_id, name="Список с items", items=[item]))

    retrieved = repo.get_by_id(saved.id)
    assert retrieved is not None
    assert retrieved.name == "Список с items"
    assert len(retrieved.items) == 1
    assert retrieved.items[0].product_name == "Яйца"
    assert retrieved.items[0].category == "Молочные"


def test_get_by_id_returns_none_when_absent(
    repo: OrmSavedShoppingListRepository,
) -> None:
    assert repo.get_by_id(SavedShoppingListId(9999)) is None


# ---------------------------------------------------------------------------
# find_all
# ---------------------------------------------------------------------------


def test_find_all_returns_only_own_lists(
    repo: OrmSavedShoppingListRepository,
    user_id: UserId,
    conn: object,
) -> None:
    from sqlalchemy import text
    from sqlalchemy.orm import Session

    session: Session = conn  # type: ignore[assignment]

    # Create a second user directly
    session.execute(
        text(
            "INSERT INTO users (email, nickname, hashed_password, created_at) "
            "VALUES ('other@example.com', 'other', 'hashed', '2025-01-01 00:00:00')"
        )
    )
    session.commit()
    other_user_id = UserId(2)

    repo.save(_make_list(user_id, name="Мой список"))
    repo.save(_make_list(other_user_id, name="Чужой список"))

    own_lists = repo.find_all(user_id)
    assert len(own_lists) == 1
    assert own_lists[0].name == "Мой список"


def test_find_all_orders_by_created_at_desc(
    repo: OrmSavedShoppingListRepository, user_id: UserId
) -> None:
    older = datetime(2026, 1, 1, 10, 0, 0, tzinfo=UTC)
    newer = datetime(2026, 3, 1, 10, 0, 0, tzinfo=UTC)

    repo.save(_make_list(user_id, name="Старый список", created_at=older))
    repo.save(_make_list(user_id, name="Новый список", created_at=newer))

    lists = repo.find_all(user_id)
    assert len(lists) == 2
    assert lists[0].name == "Новый список"
    assert lists[1].name == "Старый список"


def test_find_all_returns_empty_when_no_lists(
    repo: OrmSavedShoppingListRepository, user_id: UserId
) -> None:
    assert repo.find_all(user_id) == []


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------


def test_delete_removes_list(
    repo: OrmSavedShoppingListRepository, user_id: UserId
) -> None:
    saved = repo.save(_make_list(user_id))
    repo.delete([saved.id])
    assert repo.get_by_id(saved.id) is None


def test_delete_cascades_to_items(
    repo: OrmSavedShoppingListRepository, user_id: UserId, conn: object
) -> None:
    from sqlalchemy import text
    from sqlalchemy.orm import Session

    session: Session = conn  # type: ignore[assignment]

    item = _make_item(product_name="Молоко")
    saved = repo.save(_make_list(user_id, items=[item]))
    repo.delete([saved.id])

    count = session.execute(
        text(
            "SELECT COUNT(*) FROM shopping_list_items WHERE shopping_list_id = :id"
        ),
        {"id": int(saved.id)},
    ).scalar()
    assert count == 0


def test_delete_empty_list_is_noop(
    repo: OrmSavedShoppingListRepository,
) -> None:
    # Should not raise
    repo.delete([])


# ---------------------------------------------------------------------------
# item fields round-trip
# ---------------------------------------------------------------------------


def test_save_item_with_recipe_quantity(
    repo: OrmSavedShoppingListRepository, user_id: UserId
) -> None:
    item = _make_item(
        recipe_quantity=Quantity(200.0, "g"),
        quantity=Quantity(200.0, "g"),
        buy_quantity=Quantity(1.0, "kg"),
    )
    saved = repo.save(_make_list(user_id, items=[item]))
    retrieved = repo.get_by_id(saved.id)

    assert retrieved is not None
    assert retrieved.items[0].recipe_quantity is not None
    assert retrieved.items[0].recipe_quantity.amount == pytest.approx(200.0)
    assert retrieved.items[0].recipe_quantity.unit == "g"


def test_save_item_purchased_flag(
    repo: OrmSavedShoppingListRepository, user_id: UserId
) -> None:
    item = _make_item(purchased=True)
    saved = repo.save(_make_list(user_id, items=[item]))
    retrieved = repo.get_by_id(saved.id)

    assert retrieved is not None
    assert retrieved.items[0].purchased is True


def test_save_item_order_preserved(
    repo: OrmSavedShoppingListRepository, user_id: UserId
) -> None:
    items = [
        _make_item(product_name="Третий", item_order=2),
        _make_item(product_name="Первый", item_order=0),
        _make_item(product_name="Второй", item_order=1),
    ]
    saved = repo.save(_make_list(user_id, items=items))
    retrieved = repo.get_by_id(saved.id)

    assert retrieved is not None
    names = [i.product_name for i in retrieved.items]
    assert names == ["Первый", "Второй", "Третий"]
