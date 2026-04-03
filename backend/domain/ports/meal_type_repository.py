from abc import ABC, abstractmethod

from backend.domain.entities.meal_type import MealType
from backend.domain.value_objects.types import MealTypeId, UserId


class MealTypeRepository(ABC):
    @abstractmethod
    def get_by_id(self, id: MealTypeId) -> MealType | None: ...

    @abstractmethod
    def find_all(self, user_id: UserId) -> list[MealType]: ...

    @abstractmethod
    def find_by_name(self, user_id: UserId, name: str) -> MealType | None:
        """Найти тип по имени (регистронезависимый поиск)."""
        ...

    @abstractmethod
    def count_custom(self, user_id: UserId) -> int:
        """Количество пользовательских (is_system=False) типов."""
        ...

    @abstractmethod
    def save(self, meal_type: MealType) -> MealType: ...

    @abstractmethod
    def delete(self, ids: list[MealTypeId]) -> None: ...

    @abstractmethod
    def get_usage(self, meal_type_id: MealTypeId) -> list[tuple[int, str]]:
        """Возвращает список (menu_id, menu_name) для меню, содержащих слоты с данным типом."""
        ...
