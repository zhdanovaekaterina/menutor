from typing import Any

from sqlalchemy.orm import Session

from backend.domain.entities.family_member import FamilyMember
from backend.domain.ports.family_member_repository import FamilyMemberRepository
from backend.domain.value_objects.types import FamilyMemberId, PreferenceId, UserId
from backend.infrastructure.database.models import FamilyMemberPreferenceRow, FamilyMemberRow
from backend.infrastructure.repositories.base import BaseOrmRepository


class OrmFamilyMemberRepository(
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
            comment=entity.comment,
            preference_links=[
                FamilyMemberPreferenceRow(preference_id=int(pid))
                for pid in entity.preference_ids
            ],
        )

    def _update_row(self, row: Any, entity: FamilyMember) -> None:
        row.name = entity.name
        row.portion_multiplier = entity.portion_multiplier
        row.comment = entity.comment
        row.preference_links.clear()
        for pid in entity.preference_ids:
            row.preference_links.append(
                FamilyMemberPreferenceRow(preference_id=int(pid))
            )

    def _row_to_entity(self, row: Any) -> FamilyMember:
        return FamilyMember(
            id=FamilyMemberId(row.id),
            name=row.name,
            portion_multiplier=row.portion_multiplier,
            comment=row.comment or "",
            user_id=UserId(row.user_id),
            preference_ids=[
                PreferenceId(link.preference_id) for link in row.preference_links
            ],
        )

    def find_all(self, user_id: UserId) -> list[FamilyMember]:
        return self.find_all_by_user(int(user_id))
