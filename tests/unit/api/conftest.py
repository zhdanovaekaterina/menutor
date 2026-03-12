"""Fixtures for FastAPI router tests — mock container + TestClient."""

from collections.abc import Generator
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from backend.api.auth import get_current_user
from backend.api.deps import get_container
from backend.api.routers import auth, categories, family, menus, products, recipes
from backend.api.routers import shopping_list as shopping_list_router
from backend.domain.entities.user import User
from backend.domain.exceptions import (
    AppError,
    AuthenticationError,
    DomainError,
    EntityNotFoundError,
    RepositoryError,
    UserAlreadyExistsError,
)
from backend.domain.value_objects.types import UserId

TEST_USER = User(
    id=UserId(1),
    email="test@example.com",
    nickname="tester",
    hashed_password="hashed",
    created_at=datetime(2025, 1, 1, tzinfo=UTC),
)


def _build_test_app() -> FastAPI:
    """Собирает FastAPI-приложение без lifespan (для unit-тестов)."""
    test_app = FastAPI()

    @test_app.exception_handler(AuthenticationError)
    async def handle_auth(
        request: Request, exc: AuthenticationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=401,
            content={"detail": str(exc)},
            headers={"WWW-Authenticate": "Bearer"},
        )

    @test_app.exception_handler(UserAlreadyExistsError)
    async def handle_user_exists(
        request: Request, exc: UserAlreadyExistsError
    ) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @test_app.exception_handler(EntityNotFoundError)
    async def handle_not_found(
        request: Request, exc: EntityNotFoundError
    ) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @test_app.exception_handler(DomainError)
    async def handle_domain(request: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @test_app.exception_handler(RepositoryError)
    async def handle_repo(request: Request, exc: RepositoryError) -> JSONResponse:
        return JSONResponse(status_code=500, content={"detail": str(exc)})

    @test_app.exception_handler(AppError)
    async def handle_app(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    test_app.include_router(auth.router, prefix="/api")
    test_app.include_router(recipes.router, prefix="/api")
    test_app.include_router(products.router, prefix="/api")
    test_app.include_router(menus.router, prefix="/api")
    test_app.include_router(family.router, prefix="/api")
    test_app.include_router(categories.router, prefix="/api")
    test_app.include_router(shopping_list_router.router, prefix="/api")

    return test_app


@pytest.fixture
def container() -> MagicMock:
    return MagicMock()


@pytest.fixture
def client(container: MagicMock) -> Generator[TestClient, None, None]:
    """Client with auth auto-bypassed — for data-related router tests."""
    test_app = _build_test_app()
    test_app.dependency_overrides[get_container] = lambda: container
    test_app.dependency_overrides[get_current_user] = lambda: TEST_USER
    yield TestClient(test_app, raise_server_exceptions=False)
    test_app.dependency_overrides.clear()


@pytest.fixture
def unauth_client(container: MagicMock) -> Generator[TestClient, None, None]:
    """Client WITHOUT auth bypass — for testing auth behavior."""
    test_app = _build_test_app()
    test_app.dependency_overrides[get_container] = lambda: container
    yield TestClient(test_app, raise_server_exceptions=False)
    test_app.dependency_overrides.clear()
