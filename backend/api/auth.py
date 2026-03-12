"""Зависимость аутентификации — извлечение текущего пользователя из JWT."""

from fastapi import Depends, HTTPException, Request, status

from backend.api.deps import get_container
from backend.composition_root import ApplicationContainer
from backend.domain.entities.user import User
from backend.domain.exceptions import AuthenticationError


def get_current_user(
    request: Request,
    container: ApplicationContainer = Depends(get_container),
) -> User:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется авторизация",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = auth_header.removeprefix("Bearer ")
    try:
        return container.get_current_user.execute(token)
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
