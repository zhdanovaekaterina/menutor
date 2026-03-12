from backend.domain.entities.shopping_list import ShoppingList
from backend.domain.exceptions import EntityNotFoundError
from backend.domain.ports.menu_repository import MenuRepository
from backend.domain.services.shopping_list_builder import ShoppingListBuilder
from backend.domain.value_objects.types import MenuId, UserId


class GenerateShoppingList:
    def __init__(
        self,
        menu_repo: MenuRepository,
        builder: ShoppingListBuilder,
    ) -> None:
        self._menu_repo = menu_repo
        self._builder = builder

    def execute(self, menu_id: MenuId, user_id: UserId) -> ShoppingList:
        menu = self._menu_repo.get_by_id(menu_id)
        if menu is None or menu.user_id != user_id:
            raise EntityNotFoundError(f"Меню {menu_id} не найдено")
        return self._builder.build(menu)
