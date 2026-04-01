from backend.application.use_cases.crud_base import load_owned
from backend.domain.entities.menu import MenuSlot, WeeklyMenu
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
            self._repo.delete([menu_id])


class ListMenus:
    def __init__(self, repo: MenuRepository) -> None:
        self._repo = repo

    def execute(self, user_id: UserId) -> list[WeeklyMenu]:
        return self._repo.find_all(user_id)


class AddDishToSlot:
    """Add or replace an item in a menu slot (upsert by day+meal_type+item_id)."""

    def __init__(self, repo: MenuRepository) -> None:
        self._repo = repo

    def execute(self, menu_id: MenuId, slot: MenuSlot, user_id: UserId) -> WeeklyMenu:
        menu = load_owned(self._repo, menu_id, user_id, "Меню", not_found="не найдено")
        menu.add_or_replace_slot(slot)
        return self._repo.save(menu)


class MoveSlotInMenu:
    """Move an item from one cell to another atomically."""

    def __init__(self, repo: MenuRepository) -> None:
        self._repo = repo

    def execute(
        self,
        menu_id: MenuId,
        day: int,
        meal_type: str,
        user_id: UserId,
        to_day: int,
        to_meal_type: str,
        to_position: int,
        recipe_id: RecipeId | None = None,
        product_id: ProductId | None = None,
        position: int | None = None,
    ) -> WeeklyMenu:
        menu = load_owned(self._repo, menu_id, user_id, "Меню", not_found="не найдено")
        menu.move_slot(day, meal_type, recipe_id, product_id, to_day, to_meal_type, to_position, position)
        return self._repo.save(menu)


class RemoveDishFromSlot:
    """Remove all items from a (day, meal_type) cell."""

    def __init__(self, repo: MenuRepository) -> None:
        self._repo = repo

    def execute(
        self, menu_id: MenuId, day: int, meal_type: str, user_id: UserId
    ) -> WeeklyMenu:
        menu = load_owned(self._repo, menu_id, user_id, "Меню", not_found="не найдено")
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
        position: int | None = None,
    ) -> WeeklyMenu:
        menu = load_owned(self._repo, menu_id, user_id, "Меню", not_found="не найдено")
        menu.remove_item(day, meal_type, recipe_id, product_id, position)
        return self._repo.save(menu)


class ClearMenu:
    def __init__(self, repo: MenuRepository) -> None:
        self._repo = repo

    def execute(self, menu_id: MenuId, user_id: UserId) -> WeeklyMenu:
        menu = load_owned(self._repo, menu_id, user_id, "Меню", not_found="не найдено")
        menu.clear_slots()
        return self._repo.save(menu)


class CopyMenu:
    """Create a full copy of an existing menu with all its slots."""

    def __init__(self, repo: MenuRepository) -> None:
        self._repo = repo

    def execute(self, menu_id: MenuId, user_id: UserId) -> WeeklyMenu:
        source = load_owned(self._repo, menu_id, user_id, "Меню", not_found="не найдено")
        copied_slots = [
            MenuSlot(
                day=s.day,
                meal_type=s.meal_type,
                recipe_id=s.recipe_id,
                product_id=s.product_id,
                quantity=s.quantity,
                unit=s.unit,
                servings_override=s.servings_override,
                pieces_override=s.pieces_override,
                position=s.position,
                member_ids=list(s.member_ids),
            )
            for s in source.slots
        ]
        new_menu = WeeklyMenu(
            id=MenuId(0),
            name=f"Копия: {source.name}",
            slots=copied_slots,
            user_id=user_id,
        )
        return self._repo.save(new_menu)
