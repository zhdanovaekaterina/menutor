import pytest

from backend.domain.entities.menu import MenuSlot, WeeklyMenu
from backend.domain.exceptions import InvalidEntityError
from backend.domain.value_objects.types import MenuId, ProductId, RecipeId


def test_recipe_slot_valid() -> None:
    slot = MenuSlot(day=0, meal_type="обед", recipe_id=RecipeId(1))
    assert slot.recipe_id == RecipeId(1)
    assert slot.product_id is None


def test_product_slot_valid() -> None:
    slot = MenuSlot(day=0, meal_type="обед", product_id=ProductId(1),
                    quantity=200.0, unit="g")
    assert slot.product_id == ProductId(1)
    assert slot.recipe_id is None


def test_neither_recipe_nor_product_raises() -> None:
    with pytest.raises(InvalidEntityError, match="ровно одно"):
        MenuSlot(day=0, meal_type="обед")


def test_both_recipe_and_product_raises() -> None:
    with pytest.raises(InvalidEntityError, match="ровно одно"):
        MenuSlot(day=0, meal_type="обед", recipe_id=RecipeId(1),
                 product_id=ProductId(2))


# ---- WeeklyMenu.move_slot ----


def _make_menu(*slots: MenuSlot) -> WeeklyMenu:
    return WeeklyMenu(id=MenuId(1), name="test", slots=list(slots))


class TestMoveSlot:
    def test_move_to_empty_cell(self) -> None:
        slot = MenuSlot(day=0, meal_type="Завтрак", recipe_id=RecipeId(1), position=0)
        menu = _make_menu(slot)

        menu.move_slot(0, "Завтрак", RecipeId(1), None, 1, "Обед", 0)

        assert len(menu.slots) == 1
        moved = menu.slots[0]
        assert moved.day == 1
        assert moved.meal_type == "Обед"
        assert moved.position == 0
        assert moved.recipe_id == RecipeId(1)

    def test_move_shifts_target_positions(self) -> None:
        s0 = MenuSlot(day=1, meal_type="Обед", recipe_id=RecipeId(10), position=0)
        s1 = MenuSlot(day=1, meal_type="Обед", recipe_id=RecipeId(11), position=1)
        moving = MenuSlot(day=0, meal_type="Завтрак", recipe_id=RecipeId(5), position=0)
        menu = _make_menu(s0, s1, moving)

        menu.move_slot(0, "Завтрак", RecipeId(5), None, 1, "Обед", 1)

        target_slots = sorted(
            [s for s in menu.slots if s.day == 1 and s.meal_type == "Обед"],
            key=lambda s: s.position,
        )
        assert len(target_slots) == 3
        assert target_slots[0].recipe_id == RecipeId(10)
        assert target_slots[0].position == 0
        assert target_slots[1].recipe_id == RecipeId(5)
        assert target_slots[1].position == 1
        assert target_slots[2].recipe_id == RecipeId(11)
        assert target_slots[2].position == 2

    def test_move_product_slot(self) -> None:
        slot = MenuSlot(day=2, meal_type="Ужин", product_id=ProductId(3), quantity=1.0, unit="шт", position=0)
        menu = _make_menu(slot)

        menu.move_slot(2, "Ужин", None, ProductId(3), 0, "Завтрак", 0)

        assert menu.slots[0].day == 0
        assert menu.slots[0].meal_type == "Завтрак"
        assert menu.slots[0].product_id == ProductId(3)

    def test_move_nonexistent_slot_raises(self) -> None:
        menu = _make_menu()

        with pytest.raises(InvalidEntityError, match="не найден"):
            menu.move_slot(0, "Завтрак", RecipeId(99), None, 1, "Обед", 0)

    def test_move_within_same_cell_reorders(self) -> None:
        s0 = MenuSlot(day=0, meal_type="Завтрак", recipe_id=RecipeId(1), position=0)
        s1 = MenuSlot(day=0, meal_type="Завтрак", recipe_id=RecipeId(2), position=1)
        s2 = MenuSlot(day=0, meal_type="Завтрак", recipe_id=RecipeId(3), position=2)
        menu = _make_menu(s0, s1, s2)

        menu.move_slot(0, "Завтрак", RecipeId(3), None, 0, "Завтрак", 0)

        cell = sorted(menu.slots, key=lambda s: s.position)
        assert cell[0].recipe_id == RecipeId(3)
        assert cell[0].position == 0
        assert cell[1].recipe_id == RecipeId(1)
        assert cell[1].position == 1
        assert cell[2].recipe_id == RecipeId(2)
        assert cell[2].position == 2
