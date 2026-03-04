from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from src.domain.entities.recipe import Recipe

COLUMNS = ["Название", "Категория", "Теги", "Порций"]


class RecipeTableModel(QAbstractTableModel):
    """Qt-модель таблицы рецептов."""

    def __init__(self, recipes: list[Recipe] | None = None) -> None:
        super().__init__()
        self._recipes: list[Recipe] = recipes or []

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._recipes)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
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

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> object:
        if not index.isValid() or not (0 <= index.row() < len(self._recipes)):
            return None
        recipe = self._recipes[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            col = index.column()
            if col == 0:
                return recipe.name
            if col == 1:
                return recipe.category
            if col == 2:
                return ", ".join(recipe.dietary_tags)
            if col == 3:
                return str(recipe.servings)
        if role == Qt.ItemDataRole.UserRole:
            return recipe.id
        return None

    def set_recipes(self, recipes: list[Recipe]) -> None:
        self.beginResetModel()
        self._recipes = list(recipes)
        self.endResetModel()

    def recipe_at(self, row: int) -> Recipe | None:
        if 0 <= row < len(self._recipes):
            return self._recipes[row]
        return None
