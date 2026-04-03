from dataclasses import dataclass
from datetime import time

from backend.application.use_cases.crud_base import load_owned
from backend.domain.entities.meal_type import MealType
from backend.domain.exceptions import (
    DuplicateNameError,
    MealTypeLimitError,
    SystemMealTypeDeletionError,
)
from backend.domain.ports.meal_type_repository import MealTypeRepository
from backend.domain.value_objects.types import MealTypeId, UserId


SYSTEM_MEAL_TYPES = [
    ("Завтрак", time(8, 0), 0),
    ("Обед", time(13, 0), 1),
    ("Ужин", time(18, 0), 2),
]


@dataclass
class MealTypeData:
    name: str
    time: time


class ListMealTypes:
    def __init__(self, repo: MealTypeRepository) -> None:
        self._repo = repo

    def execute(self, user_id: UserId) -> list[MealType]:
        types = self._repo.find_all(user_id)
        return sorted(types, key=lambda t: (t.time, t.sort_order, t.id))


class CreateMealType:
    def __init__(self, repo: MealTypeRepository) -> None:
        self._repo = repo

    def execute(self, data: MealTypeData, user_id: UserId) -> MealType:
        name = data.name.strip()
        if not name or len(name) > MealType.MAX_NAME_LENGTH:
            raise ValueError("Название должно быть от 1 до 50 символов")

        if self._repo.find_by_name(user_id, name) is not None:
            raise DuplicateNameError("тип приема пищи")

        if self._repo.count_custom(user_id) >= MealType.MAX_CUSTOM_PER_USER:
            raise MealTypeLimitError(
                "Достигнут лимит типов приемов пищи (10 пользовательских)"
            )

        # sort_order: следующий после максимального
        existing = self._repo.find_all(user_id)
        max_order = max((t.sort_order for t in existing), default=-1)

        meal_type = MealType(
            id=MealTypeId(0),
            user_id=user_id,
            name=name,
            time=data.time,
            is_system=False,
            sort_order=max_order + 1,
        )
        return self._repo.save(meal_type)


class UpdateMealType:
    def __init__(self, repo: MealTypeRepository) -> None:
        self._repo = repo

    def execute(
        self, meal_type_id: MealTypeId, data: MealTypeData, user_id: UserId
    ) -> MealType:
        mt = load_owned(
            self._repo, meal_type_id, user_id,
            "Тип приема пищи", not_found="не найден",
        )
        name = data.name.strip()
        if not name or len(name) > MealType.MAX_NAME_LENGTH:
            raise ValueError("Название должно быть от 1 до 50 символов")

        existing = self._repo.find_by_name(user_id, name)
        if existing is not None and existing.id != meal_type_id:
            raise DuplicateNameError("тип приема пищи")

        mt.name = name
        mt.time = data.time
        return self._repo.save(mt)


class DeleteMealType:
    def __init__(self, repo: MealTypeRepository) -> None:
        self._repo = repo

    def execute(self, meal_type_id: MealTypeId, user_id: UserId) -> None:
        mt = load_owned(
            self._repo, meal_type_id, user_id,
            "Тип приема пищи", not_found="не найден",
        )
        if mt.is_system:
            raise SystemMealTypeDeletionError(
                "Системные типы приемов пищи нельзя удалить"
            )
        self._repo.delete([meal_type_id])


class CheckMealTypeUsage:
    """Проверяет использование типа в меню. Возвращает список (menu_id, menu_name)."""

    def __init__(self, repo: MealTypeRepository) -> None:
        self._repo = repo

    def execute(
        self, meal_type_id: MealTypeId, user_id: UserId
    ) -> list[tuple[int, str]]:
        load_owned(
            self._repo, meal_type_id, user_id,
            "Тип приема пищи", not_found="не найден",
        )
        return self._repo.get_usage(meal_type_id)


class CreateSystemMealTypes:
    """Создаёт 3 системных типа для нового пользователя."""

    def __init__(self, repo: MealTypeRepository) -> None:
        self._repo = repo

    def execute(self, user_id: UserId) -> list[MealType]:
        result = []
        for name, meal_time, order in SYSTEM_MEAL_TYPES:
            mt = MealType(
                id=MealTypeId(0),
                user_id=user_id,
                name=name,
                time=meal_time,
                is_system=True,
                sort_order=order,
            )
            result.append(self._repo.save(mt))
        return result
