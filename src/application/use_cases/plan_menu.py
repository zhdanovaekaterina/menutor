from src.domain.entities.menu import MenuSlot, WeeklyMenu
from src.domain.ports.menu_repository import MenuRepository
from src.domain.value_objects.types import MenuId


class CreateMenu:
    def __init__(self, repo: MenuRepository) -> None:
        self._repo = repo

    def execute(self, name: str) -> WeeklyMenu:
        menu = WeeklyMenu(id=MenuId(0), name=name, slots=[])
        return self._repo.save(menu)


class SaveMenu:
    def __init__(self, repo: MenuRepository) -> None:
        self._repo = repo

    def execute(self, menu: WeeklyMenu) -> WeeklyMenu:
        return self._repo.save(menu)


class LoadMenu:
    def __init__(self, repo: MenuRepository) -> None:
        self._repo = repo

    def execute(self, menu_id: MenuId) -> WeeklyMenu | None:
        return self._repo.get_by_id(menu_id)


class DeleteMenu:
    def __init__(self, repo: MenuRepository) -> None:
        self._repo = repo

    def execute(self, menu_id: MenuId) -> None:
        self._repo.delete(menu_id)


class ListMenus:
    def __init__(self, repo: MenuRepository) -> None:
        self._repo = repo

    def execute(self) -> list[WeeklyMenu]:
        return self._repo.find_all()


class AddDishToSlot:
    def __init__(self, repo: MenuRepository) -> None:
        self._repo = repo

    def execute(self, menu_id: MenuId, slot: MenuSlot) -> WeeklyMenu:
        menu = self._repo.get_by_id(menu_id)
        if menu is None:
            raise ValueError(f"Меню {menu_id} не найдено")
        menu.slots = [
            s for s in menu.slots
            if not (s.day == slot.day and s.meal_type == slot.meal_type)
        ]
        menu.slots.append(slot)
        return self._repo.save(menu)


class RemoveDishFromSlot:
    def __init__(self, repo: MenuRepository) -> None:
        self._repo = repo

    def execute(self, menu_id: MenuId, day: int, meal_type: str) -> WeeklyMenu:
        menu = self._repo.get_by_id(menu_id)
        if menu is None:
            raise ValueError(f"Меню {menu_id} не найдено")
        menu.slots = [
            s for s in menu.slots
            if not (s.day == day and s.meal_type == meal_type)
        ]
        return self._repo.save(menu)


class ClearMenu:
    def __init__(self, repo: MenuRepository) -> None:
        self._repo = repo

    def execute(self, menu_id: MenuId) -> WeeklyMenu:
        menu = self._repo.get_by_id(menu_id)
        if menu is None:
            raise ValueError(f"Меню {menu_id} не найдено")
        menu.slots = []
        return self._repo.save(menu)
