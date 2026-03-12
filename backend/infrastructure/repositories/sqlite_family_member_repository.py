from typing import Any

from sqlalchemy.orm import Session

from backend.domain.entities.family_member import FamilyMember
from backend.domain.ports.family_member_repository import FamilyMemberRepository
from backend.domain.value_objects.types import FamilyMemberId, UserId
from backend.infrastructure.database.models import FamilyMemberRow
from backend.infrastructure.repositories.base import BaseOrmRepository


class SqliteFamilyMemberRepository(
    BaseOrmRepository[FamilyMember, FamilyMemberId],
    FamilyMemberRepository,
):
    _row_class = FamilyMemberRow

    def __init__(self, session: Session) -> None:
        super().__init__(session)

    def _get_entity_id(self, entity: FamilyMember) -> int:
        return entity.id

    def _wrap_id(self, raw_id: int) -> FamilyMemberId:
        return FamilyMemberId(raw_id)

    def _make_new_row(self, entity: FamilyMember) -> FamilyMemberRow:
        return FamilyMemberRow(
            user_id=int(entity.user_id),
            name=entity.name,
            portion_multiplier=entity.portion_multiplier,
            dietary_restrictions=entity.dietary_restrictions,
            comment=entity.comment,
        )

    def _update_row(self, row: Any, entity: FamilyMember) -> None:
        row.name = entity.name
        row.portion_multiplier = entity.portion_multiplier
        row.dietary_restrictions = entity.dietary_restrictions
        row.comment = entity.comment

    def _row_to_entity(self, row: Any) -> FamilyMember:
        return FamilyMember(
            id=FamilyMemberId(row.id),
            name=row.name,
            portion_multiplier=row.portion_multiplier,
            dietary_restrictions=row.dietary_restrictions or "",
            comment=row.comment or "",
            user_id=UserId(row.user_id),
        )

    def find_all(self, user_id: UserId) -> list[FamilyMember]:
        rows = (
            self._session.query(FamilyMemberRow)
            .filter(FamilyMemberRow.user_id == int(user_id))
            .all()
        )
        return [self._row_to_entity(r) for r in rows]
