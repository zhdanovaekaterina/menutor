import hashlib
import secrets
from datetime import UTC, datetime, timedelta

import jwt

from backend.domain.services.token_service import TokenService
from backend.domain.value_objects.types import UserId

ACCESS_TOKEN_MINUTES = 30


class JwtTokenService(TokenService):
    def __init__(self, secret_key: str) -> None:
        self._secret = secret_key

    def create_access_token(self, user_id: UserId) -> str:
        payload = {
            "sub": str(int(user_id)),
            "exp": datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_MINUTES),
            "type": "access",
        }
        return jwt.encode(payload, self._secret, algorithm="HS256")

    def create_refresh_token(self, user_id: UserId) -> str:
        return secrets.token_urlsafe(64)

    def validate_access_token(self, token: str) -> UserId | None:
        try:
            payload = jwt.decode(token, self._secret, algorithms=["HS256"])
            if payload.get("type") != "access":
                return None
            return UserId(int(payload["sub"]))
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return None

    def get_refresh_token_hash(self, token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()
