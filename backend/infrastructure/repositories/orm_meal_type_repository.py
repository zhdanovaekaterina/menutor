from datetime import time
from typing import Any

from sqlalchemy.orm import Session

from backend.domain.entities.meal_type import MealType
from backend.domain.ports.meal_type_repository import MealTypeRepository
from backend.domain.value_objects.types import MealTypeId, UserId
from backend.infrastructure.database.models import MealTypeRow, MenuRow, MenuSlotRow
from backend.infrastructure.repositories.base import BaseOrmRepository


class OrmMealTypeRepository(
    BaseOrmRepository[MealType, MealTypeId],
    MealTypeRepository,
):
    _row_class = MealTypeRow

    def __init__(self, session: Session) -> None:
        super().__init__(session)

    def _get_entity_id(self, entity: MealType) -> int:
        return entity.id

    def _wrap_id(self, raw_id: int) -> MealTypeId:
        return MealTypeId(raw_id)

    def _make_new_row(self, entity: MealType) -> MealTypeRow:
        return MealTypeRow(
            user_id=int(entity.user_id),
            name=entity.name,
            time=entity.time.strftime("%H:%M"),
            is_system=entity.is_system,
            sort_order=entity.sort_order,
        )

    def _update_row(self, row: Any, entity: MealType) -> None:
        row.name = entity.name
        row.time = entity.time.strftime("%H:%M")
        # is_system not updated (BR-4)
        row.sort_order = entity.sort_order

    def _row_to_entity(self, row: Any) -> MealType:
        h, m = row.time.split(":")
        return MealType(
            id=MealTypeId(row.id),
            user_id=UserId(row.user_id),
            name=row.name,
            time=time(int(h), int(m)),
            is_system=bool(row.is_system),
            sort_order=row.sort_order,
        )

    def find_all(self, user_id: UserId) -> list[MealType]:
        return self.find_all_by_user(int(user_id))

    def find_by_name(self, user_id: UserId, name: str) -> MealType | None:
        from sqlalchemy import func

        row = (
            self._session.query(MealTypeRow)
            .filter(
                MealTypeRow.user_id == int(user_id),
                func.lower(MealTypeRow.name) == name.lower(),
            )
            .first()
        )
        return self._row_to_entity(row) if row else None

    def count_custom(self, user_id: UserId) -> int:
        return (
            self._session.query(MealTypeRow)
            .filter(
                MealTypeRow.user_id == int(user_id),
                MealTypeRow.is_system == False,  # noqa: E712
            )
            .count()
        )

    def get_usage(self, meal_type_id: MealTypeId) -> list[tuple[int, str]]:
        rows = (
            self._session.query(MenuRow.id, MenuRow.name)
            .join(MenuSlotRow, MenuRow.id == MenuSlotRow.menu_id)
            .filter(MenuSlotRow.meal_type_id == int(meal_type_id))
            .distinct()
            .all()
        )
        return [(r.id, r.name) for r in rows]
