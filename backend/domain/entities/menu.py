from dataclasses import dataclass, field

from backend.domain.exceptions import InvalidEntityError
from backend.domain.value_objects.types import (
    FamilyMemberId,
    MealTypeId,
    MenuId,
    ProductId,
    RecipeId,
    UserId,
)


@dataclass
class MenuSlot:
    day: int  # 0–6 (Mon–Sun)
    meal_type_id: MealTypeId
    recipe_id: RecipeId | None = field(default=None)
    product_id: ProductId | None = field(default=None)
    quantity: float | None = field(default=None)
    unit: str | None = field(default=None)
    servings_override: float | None = field(default=None)
    pieces_override: int | None = field(default=None)
    position: int = 0
    member_ids: list[FamilyMemberId] = field(default_factory=list)

    def __post_init__(self) -> None:
        has_recipe = self.recipe_id is not None
        has_product = self.product_id is not None
        if has_recipe == has_product:
            raise InvalidEntityError(
                "MenuSlot должен содержать ровно одно: recipe_id или product_id"
            )


@dataclass
class WeeklyMenu:
    id: MenuId
    name: str
    slots: list[MenuSlot] = field(default_factory=list)
    user_id: UserId = field(default=UserId(0))

    def add_or_replace_slot(self, slot: MenuSlot) -> None:
        """Add or replace an item (upsert by day+meal_type_id+item_id)."""
        existing = next(
            (s for s in self.slots if self._same_item(s, slot)), None
        )
        if existing is not None and slot.position == 0:
            slot.position = existing.position
        elif existing is None and slot.position == 0:
            cell_slots = [
                s
                for s in self.slots
                if s.day == slot.day and s.meal_type_id == slot.meal_type_id
            ]
            slot.position = max((s.position for s in cell_slots), default=-1) + 1
        self.slots = [s for s in self.slots if not self._same_item(s, slot)]
        self.slots.append(slot)

    def move_slot(
        self,
        day: int,
        meal_type_id: MealTypeId,
        recipe_id: RecipeId | None,
        product_id: ProductId | None,
        to_day: int,
        to_meal_type_id: MealTypeId,
        to_position: int,
        position: int | None = None,
    ) -> None:
        """Move an item from one cell to another (or reposition within the same cell)."""
        slot = next(
            (
                s
                for s in self.slots
                if s.day == day
                and s.meal_type_id == meal_type_id
                and (position is None or s.position == position)
                and (
                    (recipe_id is not None and s.recipe_id == recipe_id)
                    or (product_id is not None and s.product_id == product_id)
                )
            ),
            None,
        )
        if slot is None:
            raise InvalidEntityError("Элемент не найден в указанном слоте")

        # Remove from source cell
        self.slots.remove(slot)

        # Shift positions in target cell to make room
        target_slots = [
            s
            for s in self.slots
            if s.day == to_day and s.meal_type_id == to_meal_type_id
        ]
        for s in target_slots:
            if s.position >= to_position:
                s.position += 1

        # Place the slot in the target cell
        slot.day = to_day
        slot.meal_type_id = to_meal_type_id
        slot.position = to_position
        self.slots.append(slot)

    def remove_item(
        self,
        day: int,
        meal_type_id: MealTypeId,
        recipe_id: RecipeId | None = None,
        product_id: ProductId | None = None,
        position: int | None = None,
    ) -> None:
        """Remove a specific item from a (day, meal_type_id) cell."""
        def matches(s: MenuSlot) -> bool:
            if s.day != day or s.meal_type_id != meal_type_id:
                return False
            if position is not None and s.position != position:
                return False
            if recipe_id is not None and s.recipe_id == recipe_id:
                return True
            if product_id is not None and s.product_id == product_id:
                return True
            return False

        self.slots = [s for s in self.slots if not matches(s)]

    def clear_slots(self) -> None:
        """Remove all slots."""
        self.slots = []

    @staticmethod
    def _same_item(existing: MenuSlot, new: MenuSlot) -> bool:
        if existing.day != new.day or existing.meal_type_id != new.meal_type_id:
            return False
        if new.product_id is not None and existing.product_id == new.product_id:
            return True
        if new.recipe_id is not None and existing.recipe_id == new.recipe_id:
            return sorted(existing.member_ids) == sorted(new.member_ids)
        return False
