from typing import NamedTuple


class ActiveCategory(NamedTuple):
    """Активная категория (id, name) — совместима с tuple для dict() конвертации."""

    id: int
    name: str


class Category(NamedTuple):
    """Категория с флагом активности (id, name, active)."""

    id: int
    name: str
    active: bool
