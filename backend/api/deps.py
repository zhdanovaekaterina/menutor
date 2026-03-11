"""FastAPI dependency injection — предоставляет use-case объекты из контейнера."""

from fastapi import Request

from backend.composition_root import ApplicationContainer


def get_container(request: Request) -> ApplicationContainer:
    return request.app.state.container  # type: ignore[no-any-return]
