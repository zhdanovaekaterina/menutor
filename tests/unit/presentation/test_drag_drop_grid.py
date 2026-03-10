"""Tests for DragDropGrid and GridCell — item management, grid structure, slots."""

from unittest.mock import MagicMock

from PySide6.QtWidgets import QApplication

from backend.presentation.widgets.drag_drop_grid import (
    DAYS,
    DEFAULT_MEAL_TYPES,
    DragDropGrid,
)
from backend.presentation.widgets.grid_cell import GridCell

# ---- GridCell ----


class TestGridCell:
    def test_add_item(self, qapp: QApplication) -> None:
        cell = GridCell(day=0, meal_type="Завтрак", product_units={})
        cell.add_item("recipe", 1, "Блины", servings=2.0)
        items = cell.get_items()
        assert len(items) == 1
        assert items[0]["type"] == "recipe"
        assert items[0]["id"] == 1
        assert items[0]["name"] == "Блины"
        assert items[0]["servings"] == 2.0

    def test_add_product_item(self, qapp: QApplication) -> None:
        cell = GridCell(day=1, meal_type="Обед", product_units={})
        cell.add_item("product", 5, "Молоко", quantity=1.5, unit="l")
        items = cell.get_items()
        assert len(items) == 1
        assert items[0]["type"] == "product"
        assert items[0]["quantity"] == 1.5
        assert items[0]["unit"] == "l"

    def test_add_multiple_items(self, qapp: QApplication) -> None:
        cell = GridCell(day=0, meal_type="Завтрак", product_units={})
        cell.add_item("recipe", 1, "Блины")
        cell.add_item("product", 2, "Хлеб", quantity=1.0, unit="pcs")
        assert len(cell.get_items()) == 2

    def test_remove_item(self, qapp: QApplication) -> None:
        cell = GridCell(day=0, meal_type="Завтрак", product_units={})
        cell.add_item("recipe", 1, "Блины")
        cell.add_item("recipe", 2, "Каша")
        cell.remove_item("recipe", 1)
        items = cell.get_items()
        assert len(items) == 1
        assert items[0]["id"] == 2

    def test_remove_nonexistent_item_is_no_op(self, qapp: QApplication) -> None:
        cell = GridCell(day=0, meal_type="Завтрак", product_units={})
        cell.add_item("recipe", 1, "Блины")
        cell.remove_item("recipe", 999)
        assert len(cell.get_items()) == 1

    def test_clear(self, qapp: QApplication) -> None:
        cell = GridCell(day=0, meal_type="Завтрак", product_units={})
        cell.add_item("recipe", 1, "Блины")
        cell.add_item("recipe", 2, "Каша")
        cell.clear()
        assert len(cell.get_items()) == 0

    def test_get_items_returns_copy(self, qapp: QApplication) -> None:
        cell = GridCell(day=0, meal_type="Завтрак", product_units={})
        cell.add_item("recipe", 1, "Блины")
        items = cell.get_items()
        items.clear()
        assert len(cell.get_items()) == 1

    def test_set_default_servings(self, qapp: QApplication) -> None:
        cell = GridCell(day=0, meal_type="Завтрак", product_units={})
        cell.set_default_servings(4.0)
        assert cell._default_servings == 4.0

    def test_set_default_servings_minimum_is_one(self, qapp: QApplication) -> None:
        cell = GridCell(day=0, meal_type="Завтрак", product_units={})
        cell.set_default_servings(0.5)
        assert cell._default_servings == 1.0

    def test_find_item(self, qapp: QApplication) -> None:
        cell = GridCell(day=0, meal_type="Завтрак", product_units={})
        cell.add_item("recipe", 1, "Блины")
        assert cell._find_item("recipe", 1) is not None
        assert cell._find_item("recipe", 99) is None
        assert cell._find_item("product", 1) is None

    def test_accepts_drops(self, qapp: QApplication) -> None:
        cell = GridCell(day=0, meal_type="Завтрак", product_units={})
        assert cell.acceptDrops()


# ---- DragDropGrid ----


class TestDragDropGrid:
    def test_grid_dimensions(self, qapp: QApplication) -> None:
        grid = DragDropGrid()
        assert len(grid._cells) == 7 * 3  # 7 days × 3 meal types

    def test_grid_custom_meal_types(self, qapp: QApplication) -> None:
        grid = DragDropGrid(meal_types=["Завтрак", "Обед"])
        assert len(grid._cells) == 7 * 2

    def test_add_slot_item(self, qapp: QApplication) -> None:
        grid = DragDropGrid()
        grid.add_slot_item(0, "Завтрак", "recipe", 1, "Блины", servings=2.0)
        cell = grid._cells[(0, "Завтрак")]
        items = cell.get_items()
        assert len(items) == 1
        assert items[0]["name"] == "Блины"

    def test_add_slot_item_invalid_cell_is_no_op(self, qapp: QApplication) -> None:
        grid = DragDropGrid()
        grid.add_slot_item(0, "НесуществующийТип", "recipe", 1, "X")
        # No error, just ignored

    def test_clear_slot_item(self, qapp: QApplication) -> None:
        grid = DragDropGrid()
        grid.add_slot_item(0, "Завтрак", "recipe", 1, "Блины")
        grid.clear_slot_item(0, "Завтрак", "recipe", 1)
        cell = grid._cells[(0, "Завтрак")]
        assert len(cell.get_items()) == 0

    def test_clear_all(self, qapp: QApplication) -> None:
        grid = DragDropGrid()
        grid.add_slot_item(0, "Завтрак", "recipe", 1, "Блины")
        grid.add_slot_item(1, "Обед", "product", 2, "Хлеб", quantity=1.0, unit="pcs")
        grid.clear_all()
        for cell in grid._cells.values():
            assert len(cell.get_items()) == 0

    def test_get_slots(self, qapp: QApplication) -> None:
        grid = DragDropGrid()
        grid.add_slot_item(0, "Завтрак", "recipe", 1, "Блины", servings=2.0)
        grid.add_slot_item(3, "Ужин", "product", 5, "Хлеб", quantity=1.0, unit="pcs")
        slots = grid.get_slots()
        assert len(slots) == 2
        slot_ids = {(s["day"], s["meal_type"], s["id"]) for s in slots}
        assert (0, "Завтрак", 1) in slot_ids
        assert (3, "Ужин", 5) in slot_ids

    def test_get_slots_empty_grid(self, qapp: QApplication) -> None:
        grid = DragDropGrid()
        assert grid.get_slots() == []

    def test_set_product_units(self, qapp: QApplication) -> None:
        grid = DragDropGrid()
        grid.set_product_units({1: "g", 2: "ml"})
        assert grid._product_units == {1: "g", 2: "ml"}

    def test_set_default_recipe_servings_propagates(self, qapp: QApplication) -> None:
        grid = DragDropGrid()
        grid.set_default_recipe_servings(3.0)
        for cell in grid._cells.values():
            assert cell._default_servings == 3.0

    def test_slot_changed_signal_on_item_removed(self, qapp: QApplication) -> None:
        grid = DragDropGrid()
        grid.add_slot_item(0, "Завтрак", "recipe", 1, "Блины")
        spy = MagicMock()
        grid.slot_changed.connect(spy)

        # Simulate removal via signal (as if remove button clicked)
        grid._on_item_removed(0, "Завтрак", "recipe", 1)

        spy.assert_called_once_with(0, "Завтрак", "recipe", 1, 0.0, "")
        cell = grid._cells[(0, "Завтрак")]
        assert len(cell.get_items()) == 0

    def test_days_and_meal_types_constants(self, qapp: QApplication) -> None:
        assert DAYS == ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        assert DEFAULT_MEAL_TYPES == ["Завтрак", "Обед", "Ужин"]
