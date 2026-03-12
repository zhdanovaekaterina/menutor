from backend.domain.entities.menu import MenuSlot, WeeklyMenu
from backend.domain.exceptions import EntityNotFoundError
from backend.domain.ports.menu_repository import MenuRepository
from backend.domain.value_objects.types import MenuId, ProductId, RecipeId, UserId


class CreateMenu:
    def __init__(self, repo: MenuRepository) -> None:
        self._repo = repo

    def execute(self, name: str, user_id: UserId) -> WeeklyMenu:
        menu = WeeklyMenu(id=MenuId(0), name=name, slots=[], user_id=user_id)
        return self._repo.save(menu)


class SaveMenu:
    def __init__(self, repo: MenuRepository) -> None:
        self._repo = repo

    def execute(self, menu: WeeklyMenu) -> WeeklyMenu:
        return self._repo.save(menu)


class LoadMenu:
    def __init__(self, repo: MenuRepository) -> None:
        self._repo = repo

    def execute(self, menu_id: MenuId, user_id: UserId) -> WeeklyMenu | None:
        menu = self._repo.get_by_id(menu_id)
        if menu is not None and menu.user_id != user_id:
            return None
        return menu


class DeleteMenu:
    def __init__(self, repo: MenuRepository) -> None:
        self._repo = repo

    def execute(self, menu_id: MenuId, user_id: UserId) -> None:
        menu = self._repo.get_by_id(menu_id)
        if menu is not None and menu.user_id == user_id:
            self._repo.delete(menu_id)


class ListMenus:
    def __init__(self, repo: MenuRepository) -> None:
        self._repo = repo

    def execute(self, user_id: UserId) -> list[WeeklyMenu]:
        return self._repo.find_all(user_id)


class AddDishToSlot:
    """Add or replace an item in a menu slot (upsert by day+meal_type+item_id).

    If an item with the same (day, meal_type, recipe_id) or
    (day, meal_type, product_id) already exists, it is replaced.
    Otherwise the new slot is appended.
    """

    def __init__(self, repo: MenuRepository) -> None:
        self._repo = repo

    def execute(self, menu_id: MenuId, slot: MenuSlot, user_id: UserId) -> WeeklyMenu:
        menu = self._repo.get_by_id(menu_id)
        if menu is None or menu.user_id != user_id:
            raise EntityNotFoundError(f"Меню {menu_id} не найдено")

        menu.slots = [s for s in menu.slots if not self._same_item(s, slot)]
        menu.slots.append(slot)
        return self._repo.save(menu)

    @staticmethod
    def _same_item(existing: MenuSlot, new: MenuSlot) -> bool:
        if existing.day != new.day or existing.meal_type != new.meal_type:
            return False
        if new.recipe_id is not None and existing.recipe_id == new.recipe_id:
            return True
        if new.product_id is not None and existing.product_id == new.product_id:
            return True
        return False


class RemoveDishFromSlot:
    """Remove all items from a (day, meal_type) cell."""

    def __init__(self, repo: MenuRepository) -> None:
        self._repo = repo

    def execute(
        self, menu_id: MenuId, day: int, meal_type: str, user_id: UserId
    ) -> WeeklyMenu:
        menu = self._repo.get_by_id(menu_id)
        if menu is None or menu.user_id != user_id:
            raise EntityNotFoundError(f"Меню {menu_id} не найдено")
        menu.slots = [
            s for s in menu.slots
            if not (s.day == day and s.meal_type == meal_type)
        ]
        return self._repo.save(menu)


class RemoveItemFromSlot:
    """Remove a specific item from a (day, meal_type) cell by recipe_id or product_id."""

    def __init__(self, repo: MenuRepository) -> None:
        self._repo = repo

    def execute(
        self,
        menu_id: MenuId,
        day: int,
        meal_type: str,
        user_id: UserId,
        recipe_id: RecipeId | None = None,
        product_id: ProductId | None = None,
    ) -> WeeklyMenu:
        menu = self._repo.get_by_id(menu_id)
        if menu is None or menu.user_id != user_id:
            raise EntityNotFoundError(f"Меню {menu_id} не найдено")

        def _matches(s: MenuSlot) -> bool:
            if s.day != day or s.meal_type != meal_type:
                return False
            if recipe_id is not None and s.recipe_id == recipe_id:
                return True
            if product_id is not None and s.product_id == product_id:
                return True
            return False

        menu.slots = [s for s in menu.slots if not _matches(s)]
        return self._repo.save(menu)


class ClearMenu:
    def __init__(self, repo: MenuRepository) -> None:
        self._repo = repo

    def execute(self, menu_id: MenuId, user_id: UserId) -> WeeklyMenu:
        menu = self._repo.get_by_id(menu_id)
        if menu is None or menu.user_id != user_id:
            raise EntityNotFoundError(f"Меню {menu_id} не найдено")
        menu.slots = []
        return self._repo.save(menu)
