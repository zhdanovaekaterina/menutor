from dataclasses import dataclass
from datetime import time

from backend.domain.value_objects.types import MealTypeId, UserId


@dataclass
class MealType:
    id: MealTypeId
    user_id: UserId
    name: str           # "Завтрак", "Полдник", ...
    time: time          # datetime.time, например time(8, 0)
    is_system: bool     # True для трёх базовых типов
    sort_order: int     # Вторичная сортировка при одинаковом time

    MAX_CUSTOM_PER_USER: int = 10
    MAX_NAME_LENGTH: int = 50
