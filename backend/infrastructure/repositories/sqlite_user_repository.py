from typing import Any

from sqlalchemy.orm import Session

from backend.domain.entities.user import User
from backend.domain.ports.user_repository import UserRepository
from backend.domain.value_objects.types import UserId
from backend.infrastructure.database.models import UserRow
from backend.infrastructure.repositories.base import BaseOrmRepository


class SqliteUserRepository(
    BaseOrmRepository[User, UserId],
    UserRepository,
):
    _row_class = UserRow

    def __init__(self, session: Session) -> None:
        super().__init__(session)

    def _get_entity_id(self, entity: User) -> int:
        return entity.id

    def _wrap_id(self, raw_id: int) -> UserId:
        return UserId(raw_id)

    def _make_new_row(self, entity: User) -> UserRow:
        return UserRow(
            email=entity.email,
            nickname=entity.nickname,
            hashed_password=entity.hashed_password,
            created_at=entity.created_at,
        )

    def _update_row(self, row: Any, entity: User) -> None:
        row.email = entity.email
        row.nickname = entity.nickname
        row.hashed_password = entity.hashed_password

    def _row_to_entity(self, row: Any) -> User:
        return User(
            id=UserId(row.id),
            email=row.email,
            nickname=row.nickname,
            hashed_password=row.hashed_password,
            created_at=row.created_at,
        )

    def get_by_email(self, email: str) -> User | None:
        row = (
            self._session.query(UserRow)
            .filter(UserRow.email == email)
            .first()
        )
        if row is None:
            return None
        return self._row_to_entity(row)
