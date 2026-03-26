from dataclasses import dataclass, field
from typing import Generic, TypeVar

T = TypeVar("T")

PAGE_SIZE = 25


@dataclass
class PaginatedResult(Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
