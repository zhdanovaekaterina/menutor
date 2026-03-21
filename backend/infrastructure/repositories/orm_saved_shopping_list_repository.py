from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from backend.domain.entities.saved_shopping_list import (
    SavedShoppingList,
    SavedShoppingListItem,
)
from backend.domain.ports.saved_shopping_list_repository import (
    SavedShoppingListRepository,
)
from backend.domain.value_objects.money import Money
from backend.domain.value_objects.quantity import Quantity
from backend.domain.value_objects.types import (
    MenuId,
    ProductId,
    SavedShoppingListId,
    SavedShoppingListItemId,
    UserId,
)
from backend.infrastructure.database.models import (
    ShoppingListItemRow,
    ShoppingListRow,
)
from backend.infrastructure.repositories.base import BaseOrmRepository


class OrmSavedShoppingListRepository(
    BaseOrmRepository[SavedShoppingList, SavedShoppingListId],
    SavedShoppingListRepository,
):
    _row_class = ShoppingListRow

    def __init__(self, session: Session) -> None:
        super().__init__(session)

    def _get_entity_id(self, entity: SavedShoppingList) -> int:
        return entity.id

    def _wrap_id(self, raw_id: int) -> SavedShoppingListId:
        return SavedShoppingListId(raw_id)

    def _make_new_row(self, entity: SavedShoppingList) -> ShoppingListRow:
        row = ShoppingListRow(
            user_id=int(entity.user_id),
            name=entity.name,
            source_menu_id=int(entity.source_menu_id)
            if entity.source_menu_id is not None
            else None,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
        row.items = [self._item_to_row(item) for item in entity.items]
        return row

    def _update_row(self, row: Any, entity: SavedShoppingList) -> None:
        row.name = entity.name
        row.source_menu_id = (
            int(entity.source_menu_id) if entity.source_menu_id is not None else None
        )
        row.updated_at = entity.updated_at
        row.items = [self._item_to_row(item) for item in entity.items]

    def _row_to_entity(self, row: Any) -> SavedShoppingList:
        items = [
            SavedShoppingListItem(
                id=SavedShoppingListItemId(item.id),
                product_id=ProductId(item.product_id)
                if item.product_id is not None
                else None,
                product_name=item.product_name,
                category=item.category,
                quantity=Quantity(item.quantity_amount, item.quantity_unit),
                buy_quantity=Quantity(item.buy_quantity_amount, item.buy_quantity_unit),
                buy_quantity_overridden=bool(item.buy_quantity_overridden),
                recipe_quantity=Quantity(
                    item.recipe_quantity_amount, item.recipe_quantity_unit
                )
                if item.recipe_quantity_amount is not None
                and item.recipe_quantity_unit is not None
                else None,
                cost=Money(Decimal(str(item.cost_amount)), item.cost_currency),
                purchased=bool(item.purchased),
                item_order=item.item_order,
            )
            for item in sorted(row.items, key=lambda i: i.item_order)
        ]
        return SavedShoppingList(
            id=SavedShoppingListId(row.id),
            user_id=UserId(row.user_id),
            name=row.name,
            items=items,
            source_menu_id=MenuId(row.source_menu_id)
            if row.source_menu_id is not None
            else None,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def find_all(self, user_id: UserId) -> list[SavedShoppingList]:
        rows = (
            self._session.query(ShoppingListRow)
            .filter(ShoppingListRow.user_id == int(user_id))
            .order_by(ShoppingListRow.created_at.desc())
            .all()
        )
        return [self._row_to_entity(r) for r in rows]

    @staticmethod
    def _item_to_row(item: SavedShoppingListItem) -> ShoppingListItemRow:
        return ShoppingListItemRow(
            product_id=int(item.product_id) if item.product_id is not None else None,
            product_name=item.product_name,
            category=item.category,
            quantity_amount=item.quantity.amount,
            quantity_unit=item.quantity.unit,
            buy_quantity_amount=item.buy_quantity.amount,
            buy_quantity_unit=item.buy_quantity.unit,
            buy_quantity_overridden=item.buy_quantity_overridden,
            recipe_quantity_amount=item.recipe_quantity.amount
            if item.recipe_quantity is not None
            else None,
            recipe_quantity_unit=item.recipe_quantity.unit
            if item.recipe_quantity is not None
            else None,
            cost_amount=float(item.cost.amount),
            cost_currency=item.cost.currency,
            purchased=item.purchased,
            item_order=item.item_order,
        )
