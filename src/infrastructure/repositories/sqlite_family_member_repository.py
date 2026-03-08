import sqlite3

from src.domain.entities.family_member import FamilyMember
from src.domain.ports.family_member_repository import FamilyMemberRepository
from src.domain.value_objects.types import FamilyMemberId
from src.infrastructure.repositories.base import BaseSqliteRepository


class SqliteFamilyMemberRepository(
    BaseSqliteRepository[FamilyMember, FamilyMemberId],
    FamilyMemberRepository,
):
    _table_name = "family_members"

    def _get_entity_id(self, entity: FamilyMember) -> int:
        return entity.id

    def _wrap_id(self, raw_id: int) -> FamilyMemberId:
        return FamilyMemberId(raw_id)

    def _insert(self, entity: FamilyMember) -> int:
        cursor = self._conn.execute(
            "INSERT INTO family_members "
            "(name, portion_multiplier, dietary_restrictions, comment) "
            "VALUES (?, ?, ?, ?)",
            (entity.name, entity.portion_multiplier,
             entity.dietary_restrictions, entity.comment),
        )
        last_id = cursor.lastrowid
        if last_id is None:
            raise RuntimeError("INSERT family_members did not return lastrowid")
        return last_id

    def _update(self, entity: FamilyMember) -> None:
        self._conn.execute(
            "UPDATE family_members "
            "SET name=?, portion_multiplier=?, dietary_restrictions=?, comment=? "
            "WHERE id=?",
            (entity.name, entity.portion_multiplier,
             entity.dietary_restrictions, entity.comment, entity.id),
        )

    def _row_to_entity(self, row: sqlite3.Row) -> FamilyMember:
        return FamilyMember(
            id=FamilyMemberId(row["id"]),
            name=row["name"],
            portion_multiplier=row["portion_multiplier"],
            dietary_restrictions=row["dietary_restrictions"] or "",
            comment=row["comment"] or "",
        )
