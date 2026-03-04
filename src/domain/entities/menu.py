from dataclasses import dataclass, field

from src.domain.value_objects.types import MenuId, RecipeId


@dataclass
class MenuSlot:
    day: int  # 0–6 (Mon–Sun)
    meal_type: str
    recipe_id: RecipeId
    servings_override: float | None = field(default=None)


@dataclass
class WeeklyMenu:
    id: MenuId
    name: str
    slots: list[MenuSlot] = field(default_factory=list)
