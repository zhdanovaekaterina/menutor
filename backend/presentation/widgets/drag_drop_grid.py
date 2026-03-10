from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from backend.presentation.widgets.grid_cell import GridCell

DAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
DEFAULT_MEAL_TYPES = ["Завтрак", "Обед", "Ужин"]


class DragDropGrid(QWidget):
    """Сетка 7 дней × N типов приёма пищи. Поддерживает drag-and-drop рецептов и продуктов."""

    # day, meal_type, item_type, item_id, servings_or_qty, unit
    slot_changed = Signal(int, str, str, int, float, str)

    def __init__(
        self,
        meal_types: list[str] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._meal_types = meal_types or list(DEFAULT_MEAL_TYPES)
        self._cells: dict[tuple[int, str], GridCell] = {}
        self._product_units: dict[int, str] = {}

        self._grid_widget = QWidget()
        grid = QGridLayout(self._grid_widget)
        grid.setSpacing(2)

        # Corner spacer
        grid.addWidget(QLabel(), 0, 0)

        # Day headers
        for col, day_label in enumerate(DAYS, start=1):
            lbl = QLabel(day_label)
            lbl.setAlignment(
                lbl.alignment()
                | 0x0004  # AlignHCenter
            )
            lbl.setStyleSheet("font-weight: bold; padding: 2px;")
            grid.addWidget(lbl, 0, col)

        grid.setRowStretch(0, 0)

        # Meal type rows
        for row, meal_type in enumerate(self._meal_types, start=1):
            lbl = QLabel(meal_type)
            lbl.setStyleSheet("font-weight: bold; padding: 2px;")
            grid.addWidget(lbl, row, 0)

            for col, day_idx in enumerate(range(7), start=1):
                cell = GridCell(day_idx, meal_type, self._product_units)
                cell.item_added.connect(self.slot_changed)
                cell.item_removed.connect(self._on_item_removed)
                cell.item_moved_from.connect(self._on_item_moved_from)
                grid.addWidget(cell, row, col)
                self._cells[(day_idx, meal_type)] = cell

            grid.setRowStretch(row, 1)

        scroll = QScrollArea()
        scroll.setWidget(self._grid_widget)
        scroll.setWidgetResizable(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)

    def _on_item_removed(self, day: int, meal_type: str, item_type: str, item_id: int) -> None:
        cell = self._cells.get((day, meal_type))
        if cell:
            cell.remove_item(item_type, item_id)
            self.slot_changed.emit(day, meal_type, item_type, item_id, 0.0, "")

    def _on_item_moved_from(self, source_day: int, source_meal: str, item_type: str, item_id: int) -> None:
        """Remove item from source cell after it was moved to another cell via drag."""
        source_cell = self._cells.get((source_day, source_meal))
        if source_cell:
            source_cell.remove_item(item_type, item_id)
            self.slot_changed.emit(source_day, source_meal, item_type, item_id, 0.0, "")

    def set_product_units(self, units: dict[int, str]) -> None:
        """Обновить справочник единиц измерения продуктов (product_id -> recipe_unit)."""
        self._product_units.clear()
        self._product_units.update(units)

    def set_default_recipe_servings(self, n: float) -> None:
        for cell in self._cells.values():
            cell.set_default_servings(n)

    def add_slot_item(
        self,
        day: int,
        meal_type: str,
        item_type: str,
        item_id: int,
        name: str,
        servings: float = 1.0,
        quantity: float = 0.0,
        unit: str = "",
    ) -> None:
        cell = self._cells.get((day, meal_type))
        if cell:
            cell.add_item(item_type, item_id, name, servings, quantity, unit)

    def clear_slot_item(self, day: int, meal_type: str, item_type: str, item_id: int) -> None:
        cell = self._cells.get((day, meal_type))
        if cell:
            cell.remove_item(item_type, item_id)

    def update_item_name(self, item_type: str, item_id: int, new_name: str) -> None:
        """Обновить имя элемента во всех ячейках сетки."""
        for cell in self._cells.values():
            cell.update_item_name(item_type, item_id, new_name)

    def clear_all(self) -> None:
        for cell in self._cells.values():
            cell.clear()

    def get_slots(self) -> list[dict]:
        """Возвращает заполненные слоты как список dict."""
        result: list[dict] = []
        for (day, mt), cell in self._cells.items():
            for item in cell.get_items():
                result.append({
                    "day": day,
                    "meal_type": mt,
                    "type": item["type"],
                    "id": item["id"],
                    "servings": item["servings"],
                    "quantity": item["quantity"],
                    "unit": item["unit"],
                })
        return result
