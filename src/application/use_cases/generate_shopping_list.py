from src.domain.entities.shopping_list import ShoppingList
from src.domain.ports.family_member_repository import FamilyMemberRepository
from src.domain.ports.menu_repository import MenuRepository
from src.domain.services.shopping_list_builder import ShoppingListBuilder
from src.domain.value_objects.types import MenuId


class GenerateShoppingList:
    def __init__(
        self,
        menu_repo: MenuRepository,
        family_repo: FamilyMemberRepository,
        builder: ShoppingListBuilder,
    ) -> None:
        self._menu_repo = menu_repo
        self._family_repo = family_repo
        self._builder = builder

    def execute(self, menu_id: MenuId) -> ShoppingList:
        menu = self._menu_repo.get_by_id(menu_id)
        if menu is None:
            raise ValueError(f"Меню {menu_id} не найдено")
        members = self._family_repo.find_all()
        return self._builder.build(menu, members)
