from typing import NamedTuple


class ActiveCategory(NamedTuple):
    """Активная категория (id, name, color) — совместима с tuple для dict() конвертации."""

    id: int
    name: str
    color: str | None = None


class Category(NamedTuple):
    """Категория с флагом активности (id, name, active, color)."""

    id: int
    name: str
    active: bool
    color: str | None = None
