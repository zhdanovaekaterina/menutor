from PySide6.QtCore import QAbstractTableModel, QModelIndex, QPersistentModelIndex, Qt

from src.domain.entities.recipe import Recipe

COLUMNS = ["Название", "Категория", "Порций", "Вес, г"]


class RecipeTableModel(QAbstractTableModel):
    """Qt-модель таблицы рецептов."""

    def __init__(self, recipes: list[Recipe] | None = None) -> None:
        super().__init__()
        self._all_recipes: list[Recipe] = recipes or []
        self._recipes: list[Recipe] = list(self._all_recipes)
        self._category_map: dict[int, str] = {}

    def rowCount(self, parent: QModelIndex | QPersistentModelIndex = QModelIndex()) -> int:
        return len(self._recipes)

    def columnCount(self, parent: QModelIndex | QPersistentModelIndex = QModelIndex()) -> int:
        return len(COLUMNS)

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> object:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return COLUMNS[section]
        return None

    def data(self, index: QModelIndex | QPersistentModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> object:
        if not index.isValid() or not (0 <= index.row() < len(self._recipes)):
            return None
        recipe = self._recipes[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            col = index.column()
            if col == 0:
                return recipe.name
            if col == 1:
                return self._category_map.get(recipe.category_id, "")
            if col == 2:
                return str(recipe.servings)
            if col == 3:
                return str(recipe.weight) if recipe.weight else ""
        if role == Qt.ItemDataRole.UserRole:
            return recipe.id
        return None

    def set_category_map(self, category_map: dict[int, str]) -> None:
        self._category_map = category_map

    def set_recipes(self, recipes: list[Recipe]) -> None:
        self.beginResetModel()
        self._all_recipes = list(recipes)
        self._recipes = list(recipes)
        self.endResetModel()

    def filter(self, query: str) -> None:
        q = query.strip().lower()
        self.beginResetModel()
        self._recipes = (
            self._all_recipes
            if not q
            else [r for r in self._all_recipes if q in r.name.lower()]
        )
        self.endResetModel()

    def recipe_at(self, row: int) -> Recipe | None:
        if 0 <= row < len(self._recipes):
            return self._recipes[row]
        return None
