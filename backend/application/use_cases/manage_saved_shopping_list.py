"""Use cases for managing saved shopping lists (CRUD + toggle purchased)."""

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from backend.application.use_cases.crud_base import load_owned
from backend.domain.entities.saved_shopping_list import (
    SavedShoppingList,
    SavedShoppingListItem,
)
from backend.domain.exceptions import EntityNotFoundError
from backend.domain.ports.saved_shopping_list_repository import (
    SavedShoppingListRepository,
)
from backend.domain.value_objects.money import Money
from backend.domain.value_objects.quantity import Quantity
from backend.domain.value_objects.types import (
    ProductId,
    SavedShoppingListId,
    SavedShoppingListItemId,
    UserId,
)


@dataclass
class SavedShoppingListItemData:
    """Input data for a shopping list item when creating or updating a list."""

    product_id: int | None
    product_name: str
    category: str
    quantity_amount: float
    quantity_unit: str
    buy_quantity_amount: float
    buy_quantity_unit: str
    buy_quantity_overridden: bool
    cost_amount: float
    cost_currency: str
    purchased: bool
    recipe_quantity_amount: float | None
    recipe_quantity_unit: str | None
    item_order: int


def _item_data_to_entity(data: SavedShoppingListItemData, index: int) -> SavedShoppingListItem:
    recipe_quantity = None
    if data.recipe_quantity_amount is not None and data.recipe_quantity_unit is not None:
        recipe_quantity = Quantity(
            amount=data.recipe_quantity_amount,
            unit=data.recipe_quantity_unit,
        )
    return SavedShoppingListItem(
        id=SavedShoppingListItemId(0),
        product_id=ProductId(data.product_id) if data.product_id is not None else None,
        product_name=data.product_name,
        category=data.category,
        quantity=Quantity(amount=data.quantity_amount, unit=data.quantity_unit),
        buy_quantity=Quantity(amount=data.buy_quantity_amount, unit=data.buy_quantity_unit),
        buy_quantity_overridden=data.buy_quantity_overridden,
        cost=Money(Decimal(str(data.cost_amount)), data.cost_currency),
        purchased=data.purchased,
        recipe_quantity=recipe_quantity,
        item_order=data.item_order,
    )


def _now() -> datetime:
    return datetime.now(UTC)


def _default_name(now: datetime) -> str:
    return f"Список {now.strftime('%H:%M')} {now.strftime('%d.%m.%Y')}"


class CreateSavedShoppingList:
    def __init__(self, repo: SavedShoppingListRepository) -> None:
        self._repo = repo

    def execute(self, user_id: UserId) -> SavedShoppingList:
        now = _now()
        shopping_list = SavedShoppingList(
            id=SavedShoppingListId(0),
            user_id=user_id,
            name=_default_name(now),
            items=[],
            source_menu_id=None,
            created_at=now,
            updated_at=now,
        )
        return self._repo.save(shopping_list)


class GetSavedShoppingList:
    def __init__(self, repo: SavedShoppingListRepository) -> None:
        self._repo = repo

    def execute(self, id: SavedShoppingListId, user_id: UserId) -> SavedShoppingList:
        return load_owned(self._repo, id, user_id, "Список покупок")


class ListSavedShoppingLists:
    def __init__(self, repo: SavedShoppingListRepository) -> None:
        self._repo = repo

    def execute(self, user_id: UserId) -> list[SavedShoppingList]:
        return self._repo.find_all(user_id)


class UpdateSavedShoppingList:
    def __init__(self, repo: SavedShoppingListRepository) -> None:
        self._repo = repo

    def execute(
        self,
        id: SavedShoppingListId,
        name: str,
        items: list[SavedShoppingListItemData],
        user_id: UserId,
    ) -> SavedShoppingList:
        existing = load_owned(self._repo, id, user_id, "Список покупок")
        now = _now()
        existing.name = name
        existing.items = [_item_data_to_entity(item, i) for i, item in enumerate(items)]
        existing.updated_at = now
        return self._repo.save(existing)


class RenameSavedShoppingList:
    def __init__(self, repo: SavedShoppingListRepository) -> None:
        self._repo = repo

    def execute(
        self,
        id: SavedShoppingListId,
        name: str,
        user_id: UserId,
    ) -> SavedShoppingList:
        existing = load_owned(self._repo, id, user_id, "Список покупок")
        existing.name = name
        existing.updated_at = _now()
        return self._repo.save(existing)


class DeleteSavedShoppingList:
    def __init__(self, repo: SavedShoppingListRepository) -> None:
        self._repo = repo

    def execute(self, id: SavedShoppingListId, user_id: UserId) -> None:
        existing = self._repo.get_by_id(id)
        if existing is not None and existing.user_id == user_id:
            self._repo.delete([id])


class CopySavedShoppingList:
    def __init__(self, repo: SavedShoppingListRepository) -> None:
        self._repo = repo

    def execute(self, id: SavedShoppingListId, user_id: UserId) -> SavedShoppingList:
        source = load_owned(self._repo, id, user_id, "Список покупок")
        now = _now()
        copied_items = [
            SavedShoppingListItem(
                id=SavedShoppingListItemId(0),
                product_id=item.product_id,
                product_name=item.product_name,
                category=item.category,
                quantity=item.quantity,
                buy_quantity=item.buy_quantity,
                buy_quantity_overridden=item.buy_quantity_overridden,
                cost=item.cost,
                purchased=item.purchased,
                recipe_quantity=item.recipe_quantity,
                item_order=item.item_order,
            )
            for item in source.items
        ]
        copy = SavedShoppingList(
            id=SavedShoppingListId(0),
            user_id=user_id,
            name=f"{source.name} (копия)",
            items=copied_items,
            source_menu_id=source.source_menu_id,
            created_at=now,
            updated_at=now,
        )
        return self._repo.save(copy)


class ToggleItemPurchased:
    def __init__(self, repo: SavedShoppingListRepository) -> None:
        self._repo = repo

    def execute(
        self,
        list_id: SavedShoppingListId,
        item_id: SavedShoppingListItemId,
        user_id: UserId,
    ) -> SavedShoppingList:
        shopping_list = load_owned(self._repo, list_id, user_id, "Список покупок")
        for item in shopping_list.items:
            if item.id == item_id:
                item.purchased = not item.purchased
                break
        else:
            raise EntityNotFoundError(f"Позиция {item_id} не найдена в списке {list_id}")
        shopping_list.updated_at = _now()
        return self._repo.save(shopping_list)
