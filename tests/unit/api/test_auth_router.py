"""Tests for /api/auth router."""

from datetime import UTC, datetime
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from backend.domain.entities.user import User
from backend.domain.exceptions import AuthenticationError, UserAlreadyExistsError
from backend.domain.value_objects.types import UserId


def _user(id: int = 1) -> User:
    return User(
        id=UserId(id),
        email="test@example.com",
        nickname="tester",
        hashed_password="hashed",
        created_at=datetime(2025, 1, 1, tzinfo=UTC),
    )


# ---- POST /api/auth/register ----


class TestRegister:
    def test_register_returns_201(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.register_user.execute.return_value = _user()
        body = {
            "email": "test@example.com",
            "password": "secret123",
            "nickname": "tester",
        }
        resp = client.post("/api/auth/register", json=body)
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "test@example.com"
        assert data["nickname"] == "tester"
        assert "hashed_password" not in data
        container.register_user.execute.assert_called_once()

    def test_register_minimal_fields(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.register_user.execute.return_value = _user()
        body = {"email": "test@example.com", "password": "secret123"}
        resp = client.post("/api/auth/register", json=body)
        assert resp.status_code == 201

    def test_register_returns_409_on_duplicate(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.register_user.execute.side_effect = UserAlreadyExistsError(
            "Пользователь с email test@example.com уже существует"
        )
        body = {"email": "test@example.com", "password": "secret123"}
        resp = client.post("/api/auth/register", json=body)
        assert resp.status_code == 409
        assert "уже существует" in resp.json()["detail"]

    def test_register_returns_422_on_missing_fields(
        self, client: TestClient, container: MagicMock
    ) -> None:
        resp = client.post("/api/auth/register", json={})
        assert resp.status_code == 422


# ---- POST /api/auth/login ----


class TestLogin:
    def test_login_returns_tokens(
        self, client: TestClient, container: MagicMock
    ) -> None:
        from backend.application.use_cases.auth import TokenPair

        container.login_user.execute.return_value = TokenPair(
            access_token="access.jwt.token",
            refresh_token="refresh-token-value",
        )
        body = {"email": "test@example.com", "password": "secret123"}
        resp = client.post("/api/auth/login", json=body)
        assert resp.status_code == 200
        data = resp.json()
        assert data["access_token"] == "access.jwt.token"
        assert data["refresh_token"] == "refresh-token-value"
        assert data["token_type"] == "bearer"

    def test_login_returns_401_on_bad_credentials(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.login_user.execute.side_effect = AuthenticationError(
            "Неверный email или пароль"
        )
        body = {"email": "test@example.com", "password": "wrong"}
        resp = client.post("/api/auth/login", json=body)
        assert resp.status_code == 401


# ---- POST /api/auth/refresh ----


class TestRefresh:
    def test_refresh_returns_new_tokens(
        self, client: TestClient, container: MagicMock
    ) -> None:
        from backend.application.use_cases.auth import TokenPair

        container.refresh_access_token.execute.return_value = TokenPair(
            access_token="new.access.token",
            refresh_token="new-refresh-token",
        )
        body = {"refresh_token": "old-refresh-token"}
        resp = client.post("/api/auth/refresh", json=body)
        assert resp.status_code == 200
        data = resp.json()
        assert data["access_token"] == "new.access.token"
        assert data["refresh_token"] == "new-refresh-token"

    def test_refresh_returns_401_on_invalid_token(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.refresh_access_token.execute.side_effect = AuthenticationError(
            "Refresh-токен недействителен или истёк"
        )
        body = {"refresh_token": "bad-token"}
        resp = client.post("/api/auth/refresh", json=body)
        assert resp.status_code == 401


# ---- POST /api/auth/logout ----


class TestLogout:
    def test_logout_returns_204(
        self, client: TestClient, container: MagicMock
    ) -> None:
        body = {"refresh_token": "some-refresh-token"}
        resp = client.post("/api/auth/logout", json=body)
        assert resp.status_code == 204
        container.logout_user.execute.assert_called_once_with("some-refresh-token")


# ---- GET /api/auth/me ----


class TestGetMe:
    def test_returns_user_with_valid_token(
        self, client: TestClient, container: MagicMock
    ) -> None:
        # client fixture auto-injects TEST_USER via get_current_user override
        resp = client.get("/api/auth/me")
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "test@example.com"
        assert data["nickname"] == "tester"
        assert "hashed_password" not in data

    def test_returns_401_without_token(
        self, unauth_client: TestClient, container: MagicMock
    ) -> None:
        resp = unauth_client.get("/api/auth/me")
        assert resp.status_code == 401

    def test_returns_401_with_invalid_token(
        self, unauth_client: TestClient, container: MagicMock
    ) -> None:
        container.get_current_user.execute.side_effect = AuthenticationError(
            "Токен недействителен или истёк"
        )
        resp = unauth_client.get(
            "/api/auth/me", headers={"Authorization": "Bearer bad.token"}
        )
        assert resp.status_code == 401

    def test_returns_401_with_malformed_header(
        self, unauth_client: TestClient, container: MagicMock
    ) -> None:
        resp = unauth_client.get(
            "/api/auth/me", headers={"Authorization": "NotBearer token"}
        )
        assert resp.status_code == 401


# ---- PATCH /api/auth/me ----


class TestUpdateMe:
    def test_update_nickname(
        self, client: TestClient, container: MagicMock
    ) -> None:
        # client auto-injects TEST_USER
        updated = User(
            id=UserId(1),
            email="test@example.com",
            nickname="new_nick",
            hashed_password="hashed",
            created_at=datetime(2025, 1, 1, tzinfo=UTC),
        )
        container.user_repo.save.return_value = updated
        resp = client.patch("/api/auth/me", json={"nickname": "new_nick"})
        assert resp.status_code == 200
        assert resp.json()["nickname"] == "new_nick"

    def test_update_password(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.password_hasher.hash.return_value = "new_hashed"
        container.user_repo.save.return_value = _user()
        resp = client.patch("/api/auth/me", json={"password": "newpass123"})
        assert resp.status_code == 200
        container.password_hasher.hash.assert_called_once_with("newpass123")

    def test_returns_401_without_auth(
        self, unauth_client: TestClient, container: MagicMock
    ) -> None:
        resp = unauth_client.patch("/api/auth/me", json={"nickname": "new"})
        assert resp.status_code == 401
