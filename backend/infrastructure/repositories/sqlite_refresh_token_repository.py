from sqlalchemy.orm import Session

from backend.domain.entities.refresh_token import RefreshToken
from backend.domain.ports.refresh_token_repository import RefreshTokenRepository
from backend.domain.value_objects.types import RefreshTokenId, UserId
from backend.infrastructure.database.models import RefreshTokenRow


class SqliteRefreshTokenRepository(RefreshTokenRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, token: RefreshToken) -> RefreshToken:
        row = RefreshTokenRow(
            user_id=int(token.user_id),
            token_hash=token.token_hash,
            expires_at=token.expires_at,
            revoked=token.revoked,
        )
        self._session.add(row)
        self._session.flush()
        self._session.commit()
        return RefreshToken(
            id=RefreshTokenId(row.id),
            user_id=UserId(row.user_id),
            token_hash=row.token_hash,
            expires_at=row.expires_at,
            revoked=row.revoked,
        )

    def get_by_token_hash(self, token_hash: str) -> RefreshToken | None:
        row = (
            self._session.query(RefreshTokenRow)
            .filter(RefreshTokenRow.token_hash == token_hash)
            .first()
        )
        if row is None:
            return None
        return RefreshToken(
            id=RefreshTokenId(row.id),
            user_id=UserId(row.user_id),
            token_hash=row.token_hash,
            expires_at=row.expires_at,
            revoked=row.revoked,
        )

    def revoke(self, token_hash: str) -> None:
        row = (
            self._session.query(RefreshTokenRow)
            .filter(RefreshTokenRow.token_hash == token_hash)
            .first()
        )
        if row is not None:
            row.revoked = True
            self._session.commit()

    def revoke_all_for_user(self, user_id: UserId) -> None:
        self._session.query(RefreshTokenRow).filter(
            RefreshTokenRow.user_id == int(user_id),
            RefreshTokenRow.revoked == False,  # noqa: E712
        ).update({"revoked": True})
        self._session.commit()
