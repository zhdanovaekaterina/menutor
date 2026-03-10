from backend.domain.entities.recipe import Recipe
from backend.presentation.models.base_table_model import BaseCrudTableModel


class RecipeTableModel(BaseCrudTableModel[Recipe]):
    """Qt-модель таблицы рецептов."""

    _columns = ["Название", "Категория", "Порций", "Вес, г"]

    def _entity_id(self, entity: Recipe) -> int:
        return entity.id

    def _entity_name(self, entity: Recipe) -> str:
        return entity.name

    def _display_value(self, entity: Recipe, column: int) -> str:
        if column == 0:
            return entity.name
        if column == 1:
            return self._category_map.get(entity.category_id, "")
        if column == 2:
            return str(entity.servings)
        if column == 3:
            return str(entity.weight) if entity.weight else ""
        return ""

    def set_recipes(self, recipes: list[Recipe]) -> None:
        self.set_items(recipes)

    def recipe_at(self, row: int) -> Recipe | None:
        return self.item_at(row)
