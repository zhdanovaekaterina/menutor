from abc import ABC, abstractmethod

from backend.domain.entities.saved_shopping_list import SavedShoppingList
from backend.domain.value_objects.types import SavedShoppingListId, UserId


class SavedShoppingListRepository(ABC):
    @abstractmethod
    def save(self, shopping_list: SavedShoppingList) -> SavedShoppingList: ...

    @abstractmethod
    def get_by_id(self, id: SavedShoppingListId) -> SavedShoppingList | None: ...

    @abstractmethod
    def find_all(self, user_id: UserId) -> list[SavedShoppingList]: ...

    @abstractmethod
    def delete(self, ids: list[SavedShoppingListId]) -> None: ...
