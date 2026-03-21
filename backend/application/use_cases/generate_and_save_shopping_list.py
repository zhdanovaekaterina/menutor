"""Use case: generate a shopping list from a menu and persist it as a SavedShoppingList."""

from datetime import UTC, datetime
from decimal import Decimal

from backend.domain.entities.saved_shopping_list import (
    SavedShoppingList,
    SavedShoppingListItem,
)
from backend.domain.exceptions import EntityNotFoundError
from backend.domain.ports.menu_repository import MenuRepository
from backend.domain.ports.saved_shopping_list_repository import (
    SavedShoppingListRepository,
)
from backend.domain.services.shopping_list_builder import ShoppingListBuilder
from backend.domain.value_objects.types import (
    MenuId,
    SavedShoppingListId,
    SavedShoppingListItemId,
    UserId,
)


class GenerateAndSaveShoppingList:
    def __init__(
        self,
        menu_repo: MenuRepository,
        builder: ShoppingListBuilder,
        saved_list_repo: SavedShoppingListRepository,
    ) -> None:
        self._menu_repo = menu_repo
        self._builder = builder
        self._saved_list_repo = saved_list_repo

    def execute(self, menu_id: MenuId, user_id: UserId) -> SavedShoppingList:
        menu = self._menu_repo.get_by_id(menu_id)
        if menu is None or menu.user_id != user_id:
            raise EntityNotFoundError(f"Меню {menu_id} не найдено")

        shopping_list = self._builder.build(menu)

        now = datetime.now(UTC)
        time_str = now.strftime("%H:%M")
        date_str = now.strftime("%d.%m.%Y")
        name = f'Создано из меню «{menu.name}» {time_str} {date_str}'

        items = [
            SavedShoppingListItem(
                id=SavedShoppingListItemId(0),
                product_id=item.product_id,
                product_name=item.product_name,
                category=item.category,
                quantity=item.quantity,
                buy_quantity=item.buy_quantity,
                buy_quantity_overridden=False,
                cost=item.cost,
                purchased=False,
                recipe_quantity=item.recipe_quantity,
                item_order=index,
            )
            for index, item in enumerate(shopping_list.items)
        ]

        saved = SavedShoppingList(
            id=SavedShoppingListId(0),
            user_id=user_id,
            name=name,
            items=items,
            source_menu_id=menu_id,
            created_at=now,
            updated_at=now,
        )
        return self._saved_list_repo.save(saved)
