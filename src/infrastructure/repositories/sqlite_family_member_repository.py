import sqlite3

from src.domain.entities.family_member import FamilyMember
from src.domain.ports.family_member_repository import FamilyMemberRepository
from src.domain.value_objects.types import FamilyMemberId


class SqliteFamilyMemberRepository(FamilyMemberRepository):
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    # ---- read ----

    def get_by_id(self, id: FamilyMemberId) -> FamilyMember | None:
        row = self._conn.execute(
            "SELECT * FROM family_members WHERE id = ?", (id,)
        ).fetchone()
        return self._row_to_entity(row) if row else None

    def find_all(self) -> list[FamilyMember]:
        rows = self._conn.execute("SELECT * FROM family_members").fetchall()
        return [self._row_to_entity(r) for r in rows]

    # ---- write ----

    def save(self, member: FamilyMember) -> FamilyMember:
        member_id: FamilyMemberId
        with self._conn:
            if member.id == 0:
                cursor = self._conn.execute(
                    "INSERT INTO family_members "
                    "(name, portion_multiplier, dietary_restrictions, comment) "
                    "VALUES (?, ?, ?, ?)",
                    (
                        member.name,
                        member.portion_multiplier,
                        member.dietary_restrictions,
                        member.comment,
                    ),
                )
                last_id = cursor.lastrowid
                if last_id is None:
                    raise RuntimeError("INSERT family_members did not return lastrowid")
                member_id = FamilyMemberId(last_id)
            else:
                self._conn.execute(
                    "UPDATE family_members "
                    "SET name=?, portion_multiplier=?, dietary_restrictions=?, comment=? "
                    "WHERE id=?",
                    (
                        member.name,
                        member.portion_multiplier,
                        member.dietary_restrictions,
                        member.comment,
                        member.id,
                    ),
                )
                member_id = member.id

        result = self.get_by_id(member_id)
        if result is None:
            raise RuntimeError(f"Failed to retrieve family member {member_id} after save")
        return result

    def delete(self, id: FamilyMemberId) -> None:
        with self._conn:
            self._conn.execute("DELETE FROM family_members WHERE id = ?", (id,))

    # ---- mapping ----

    def _row_to_entity(self, row: sqlite3.Row) -> FamilyMember:
        return FamilyMember(
            id=FamilyMemberId(row["id"]),
            name=row["name"],
            portion_multiplier=row["portion_multiplier"],
            dietary_restrictions=row["dietary_restrictions"] or "",
            comment=row["comment"] or "",
        )
