import pytest
from backend.domain.entities.menu import MenuSlot, WeeklyMenu
from backend.domain.value_objects.types import FamilyMemberId, MenuId, ProductId, RecipeId, UserId


def make_recipe_slot(day=0, meal="breakfast", recipe_id=1, member_ids=None, position=0):
    return MenuSlot(
        day=day, meal_type=meal,
        recipe_id=RecipeId(recipe_id),
        member_ids=[FamilyMemberId(m) for m in (member_ids or [])],
        position=position,
    )

def make_product_slot(day=0, meal="breakfast", product_id=1, member_ids=None, position=0):
    return MenuSlot(
        day=day, meal_type=meal,
        product_id=ProductId(product_id),
        member_ids=[FamilyMemberId(m) for m in (member_ids or [])],
        position=position,
    )

def make_menu():
    return WeeklyMenu(id=MenuId(1), name="Test", user_id=UserId(1))


def test_menu_slot_default_member_ids():
    slot = make_recipe_slot()
    assert slot.member_ids == []


def test_same_item_same_recipe_same_members():
    a = make_recipe_slot(recipe_id=1, member_ids=[1, 2])
    b = make_recipe_slot(recipe_id=1, member_ids=[1, 2])
    assert WeeklyMenu._same_item(a, b)


def test_same_item_same_recipe_different_members():
    a = make_recipe_slot(recipe_id=1, member_ids=[1, 2])
    b = make_recipe_slot(recipe_id=1, member_ids=[3])
    assert not WeeklyMenu._same_item(a, b)


def test_same_item_same_recipe_empty_vs_nonempty():
    a = make_recipe_slot(recipe_id=1, member_ids=[])
    b = make_recipe_slot(recipe_id=1, member_ids=[1])
    assert not WeeklyMenu._same_item(a, b)


def test_same_item_product_ignores_members():
    a = make_product_slot(product_id=1, member_ids=[])
    b = make_product_slot(product_id=1, member_ids=[1, 2])  # member_ids on products is unusual but let's test
    # products always use member_ids=[] in practice, but the _same_item logic uses product_id only
    assert WeeklyMenu._same_item(a, b)


def test_add_or_replace_creates_new_for_different_members():
    menu = make_menu()
    slot_a = make_recipe_slot(recipe_id=1, member_ids=[1, 2])
    slot_b = make_recipe_slot(recipe_id=1, member_ids=[3])
    menu.add_or_replace_slot(slot_a)
    menu.add_or_replace_slot(slot_b)
    assert len(menu.slots) == 2


def test_add_or_replace_updates_for_same_members():
    menu = make_menu()
    slot_a = make_recipe_slot(recipe_id=1, member_ids=[1, 2], position=0)
    slot_b = make_recipe_slot(recipe_id=1, member_ids=[1, 2])
    slot_b.servings_override = 5.0
    menu.add_or_replace_slot(slot_a)
    menu.add_or_replace_slot(slot_b)
    assert len(menu.slots) == 1
    assert menu.slots[0].servings_override == 5.0


def test_remove_item_by_position():
    menu = make_menu()
    slot_a = make_recipe_slot(recipe_id=1, member_ids=[1], position=0)
    slot_b = make_recipe_slot(recipe_id=1, member_ids=[2], position=1)
    menu.slots = [slot_a, slot_b]
    menu.remove_item(day=0, meal_type="breakfast", recipe_id=RecipeId(1), position=0)
    assert len(menu.slots) == 1
    assert menu.slots[0].position == 1


def test_remove_item_without_position_removes_all_matching():
    menu = make_menu()
    slot_a = make_recipe_slot(recipe_id=1, member_ids=[1], position=0)
    slot_b = make_recipe_slot(recipe_id=1, member_ids=[2], position=1)
    menu.slots = [slot_a, slot_b]
    menu.remove_item(day=0, meal_type="breakfast", recipe_id=RecipeId(1))
    assert len(menu.slots) == 0


def test_move_slot_with_position_disambiguation():
    menu = make_menu()
    slot_a = make_recipe_slot(recipe_id=1, member_ids=[1], position=0)
    slot_b = make_recipe_slot(recipe_id=1, member_ids=[2], position=1)
    menu.slots = [slot_a, slot_b]
    menu.move_slot(
        day=0, meal_type="breakfast",
        recipe_id=RecipeId(1), product_id=None,
        to_day=1, to_meal_type="lunch", to_position=0,
        position=0,
    )
    assert len(menu.slots) == 2
    moved = next(s for s in menu.slots if s.day == 1)
    assert sorted(moved.member_ids) == [FamilyMemberId(1)]


def test_member_ids_preserved_on_move():
    menu = make_menu()
    slot = make_recipe_slot(recipe_id=1, member_ids=[1, 2], position=0)
    menu.slots = [slot]
    menu.move_slot(
        day=0, meal_type="breakfast",
        recipe_id=RecipeId(1), product_id=None,
        to_day=2, to_meal_type="dinner", to_position=0,
    )
    assert sorted(menu.slots[0].member_ids) == [FamilyMemberId(1), FamilyMemberId(2)]


def test_copy_menu_copies_member_ids():
    from backend.application.use_cases.plan_menu import CopyMenu
    from unittest.mock import MagicMock

    source = make_menu()
    source.slots = [make_recipe_slot(recipe_id=1, member_ids=[1, 2])]

    repo = MagicMock()
    repo.get_by_id.return_value = source
    repo.save.side_effect = lambda m: m

    uc = CopyMenu(repo)
    copied = uc.execute(MenuId(1), UserId(1))
    assert len(copied.slots) == 1
    assert sorted(copied.slots[0].member_ids) == [FamilyMemberId(1), FamilyMemberId(2)]
    # Ensure it's a copy not the same list
    assert copied.slots[0].member_ids is not source.slots[0].member_ids
