from abc import ABC, abstractmethod

from backend.domain.entities.menu import WeeklyMenu
from backend.domain.value_objects.types import MenuId


class MenuRepository(ABC):
    @abstractmethod
    def get_by_id(self, id: MenuId) -> WeeklyMenu | None: ...

    @abstractmethod
    def find_all(self) -> list[WeeklyMenu]: ...

    @abstractmethod
    def save(self, menu: WeeklyMenu) -> WeeklyMenu: ...

    @abstractmethod
    def delete(self, id: MenuId) -> None: ...
