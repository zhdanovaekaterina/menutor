from dataclasses import dataclass, field

from backend.domain.exceptions import InvalidEntityError
from backend.domain.value_objects.types import MenuId, ProductId, RecipeId, UserId


@dataclass
class MenuSlot:
    day: int  # 0–6 (Mon–Sun)
    meal_type: str
    recipe_id: RecipeId | None = field(default=None)
    product_id: ProductId | None = field(default=None)
    quantity: float | None = field(default=None)
    unit: str | None = field(default=None)
    servings_override: float | None = field(default=None)

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
        """Add or replace an item (upsert by day+meal_type+item_id)."""
        self.slots = [s for s in self.slots if not self._same_item(s, slot)]
        self.slots.append(slot)

    def remove_item(
        self,
        day: int,
        meal_type: str,
        recipe_id: RecipeId | None = None,
        product_id: ProductId | None = None,
    ) -> None:
        """Remove a specific item from a (day, meal_type) cell."""
        def matches(s: MenuSlot) -> bool:
            if s.day != day or s.meal_type != meal_type:
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
        if existing.day != new.day or existing.meal_type != new.meal_type:
            return False
        if new.recipe_id is not None and existing.recipe_id == new.recipe_id:
            return True
        if new.product_id is not None and existing.product_id == new.product_id:
            return True
        return False
