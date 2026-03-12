from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from backend.domain.entities.refresh_token import RefreshToken
from backend.domain.entities.user import User
from backend.domain.exceptions import AuthenticationError, UserAlreadyExistsError
from backend.domain.ports.refresh_token_repository import RefreshTokenRepository
from backend.domain.ports.user_repository import UserRepository
from backend.domain.services.password_hasher import PasswordHasher
from backend.domain.services.token_service import TokenService
from backend.domain.value_objects.types import RefreshTokenId, UserId

REFRESH_TOKEN_DAYS = 30


@dataclass
class RegisterData:
    email: str
    password: str
    nickname: str = ""


@dataclass
class LoginData:
    email: str
    password: str


@dataclass
class TokenPair:
    access_token: str
    refresh_token: str


class RegisterUser:
    def __init__(
        self,
        user_repo: UserRepository,
        hasher: PasswordHasher,
    ) -> None:
        self._user_repo = user_repo
        self._hasher = hasher

    def execute(self, data: RegisterData) -> User:
        existing = self._user_repo.get_by_email(data.email)
        if existing is not None:
            raise UserAlreadyExistsError(
                f"Пользователь с email {data.email} уже существует"
            )
        user = User(
            id=UserId(0),
            email=data.email,
            nickname=data.nickname or data.email.split("@")[0],
            hashed_password=self._hasher.hash(data.password),
        )
        return self._user_repo.save(user)


class LoginUser:
    def __init__(
        self,
        user_repo: UserRepository,
        hasher: PasswordHasher,
        token_service: TokenService,
        refresh_repo: RefreshTokenRepository,
    ) -> None:
        self._user_repo = user_repo
        self._hasher = hasher
        self._token_service = token_service
        self._refresh_repo = refresh_repo

    def execute(self, data: LoginData) -> TokenPair:
        user = self._user_repo.get_by_email(data.email)
        if user is None or not self._hasher.verify(data.password, user.hashed_password):
            raise AuthenticationError("Неверный email или пароль")

        access_token = self._token_service.create_access_token(user.id)
        raw_refresh = self._token_service.create_refresh_token(user.id)

        refresh_entry = RefreshToken(
            id=RefreshTokenId(0),
            user_id=user.id,
            token_hash=self._token_service.get_refresh_token_hash(raw_refresh),
            expires_at=datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_DAYS),
        )
        self._refresh_repo.save(refresh_entry)

        return TokenPair(access_token=access_token, refresh_token=raw_refresh)


class RefreshAccessToken:
    def __init__(
        self,
        token_service: TokenService,
        refresh_repo: RefreshTokenRepository,
        user_repo: UserRepository,
    ) -> None:
        self._token_service = token_service
        self._refresh_repo = refresh_repo
        self._user_repo = user_repo

    def execute(self, raw_refresh_token: str) -> TokenPair:
        token_hash = self._token_service.get_refresh_token_hash(raw_refresh_token)
        stored = self._refresh_repo.get_by_token_hash(token_hash)

        if stored is None or stored.revoked or stored.expires_at < datetime.now(UTC):
            raise AuthenticationError("Refresh-токен недействителен или истёк")

        # Rotate: revoke old, issue new
        self._refresh_repo.revoke(token_hash)

        user = self._user_repo.get_by_id(stored.user_id)
        if user is None:
            raise AuthenticationError("Пользователь не найден")

        new_access = self._token_service.create_access_token(stored.user_id)
        new_raw_refresh = self._token_service.create_refresh_token(stored.user_id)

        new_entry = RefreshToken(
            id=RefreshTokenId(0),
            user_id=stored.user_id,
            token_hash=self._token_service.get_refresh_token_hash(new_raw_refresh),
            expires_at=datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_DAYS),
        )
        self._refresh_repo.save(new_entry)

        return TokenPair(access_token=new_access, refresh_token=new_raw_refresh)


class GetCurrentUser:
    def __init__(
        self,
        token_service: TokenService,
        user_repo: UserRepository,
    ) -> None:
        self._token_service = token_service
        self._user_repo = user_repo

    def execute(self, access_token: str) -> User:
        user_id = self._token_service.validate_access_token(access_token)
        if user_id is None:
            raise AuthenticationError("Токен недействителен или истёк")
        user = self._user_repo.get_by_id(user_id)
        if user is None:
            raise AuthenticationError("Пользователь не найден")
        return user


class LogoutUser:
    def __init__(
        self,
        token_service: TokenService,
        refresh_repo: RefreshTokenRepository,
    ) -> None:
        self._token_service = token_service
        self._refresh_repo = refresh_repo

    def execute(self, raw_refresh_token: str) -> None:
        token_hash = self._token_service.get_refresh_token_hash(raw_refresh_token)
        self._refresh_repo.revoke(token_hash)
