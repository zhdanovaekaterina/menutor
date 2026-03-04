from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

DAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
DEFAULT_MEAL_TYPES = ["Завтрак", "Обед", "Ужин"]


class _GridCell(QFrame):
    """Одна ячейка сетки меню. Принимает drag рецептов."""

    remove_clicked = Signal(int, str)  # day, meal_type
    recipe_dropped = Signal(int, str, object, float)  # day, meal_type, recipe_id, servings

    def __init__(self, day: int, meal_type: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.day = day
        self.meal_type = meal_type
        self._recipe_id: object = None
        self._servings: float = 1.0

        self.setAcceptDrops(True)
        self.setFrameShape(QFrame.Shape.Box)
        self.setMinimumSize(110, 70)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self._name_label = QLabel()
        self._name_label.setWordWrap(True)
        self._name_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )

        self._remove_btn = QPushButton("✕")
        self._remove_btn.setMaximumSize(22, 22)
        self._remove_btn.setVisible(False)
        self._remove_btn.clicked.connect(
            lambda: self.remove_clicked.emit(self.day, self.meal_type)
        )

        self._servings_label = QLabel()

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.addWidget(self._name_label, 1)
        top_row.addWidget(self._remove_btn)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addLayout(top_row)
        layout.addWidget(self._servings_label)

    def dragEnterEvent(self, event) -> None:  # type: ignore[override]
        if event.mimeData().hasFormat("application/x-menutor-recipe-id"):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:  # type: ignore[override]
        if event.mimeData().hasFormat("application/x-menutor-recipe-id"):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event) -> None:  # type: ignore[override]
        raw = event.mimeData().data("application/x-menutor-recipe-id")
        recipe_id_val = int(raw.data().decode())
        display_name = event.mimeData().text()
        self._set_recipe(recipe_id_val, display_name, 1.0)
        event.acceptProposedAction()
        self.recipe_dropped.emit(self.day, self.meal_type, recipe_id_val, 1.0)

    def _set_recipe(self, recipe_id: object, name: str, servings: float) -> None:
        self._recipe_id = recipe_id
        self._servings = servings
        self._name_label.setText(name)
        self._servings_label.setText(f"Порций: {servings:.1f}")
        self._remove_btn.setVisible(True)

    def set_recipe(self, recipe_id: object, name: str, servings: float) -> None:
        """Programmatically fill a cell (no signal emitted)."""
        self._set_recipe(recipe_id, name, servings)

    def clear(self) -> None:
        self._recipe_id = None
        self._servings = 1.0
        self._name_label.setText("")
        self._servings_label.setText("")
        self._remove_btn.setVisible(False)

    @property
    def recipe_id(self) -> object:
        return self._recipe_id

    @property
    def servings(self) -> float:
        return self._servings


class DragDropGrid(QWidget):
    """Сетка 7 дней × N типов приёма пищи. Поддерживает drag-and-drop рецептов."""

    slot_changed = Signal(int, str, object, float)  # day, meal_type, recipe_id (None=remove), servings

    def __init__(
        self,
        meal_types: list[str] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._meal_types = meal_types or list(DEFAULT_MEAL_TYPES)
        self._cells: dict[tuple[int, str], _GridCell] = {}

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

        # Meal type rows
        for row, meal_type in enumerate(self._meal_types, start=1):
            lbl = QLabel(meal_type)
            lbl.setStyleSheet("font-weight: bold; padding: 2px;")
            grid.addWidget(lbl, row, 0)

            for col, day_idx in enumerate(range(7), start=1):
                cell = _GridCell(day_idx, meal_type)
                cell.recipe_dropped.connect(self.slot_changed)
                cell.remove_clicked.connect(self._on_remove)
                grid.addWidget(cell, row, col)
                self._cells[(day_idx, meal_type)] = cell

        scroll = QScrollArea()
        scroll.setWidget(self._grid_widget)
        scroll.setWidgetResizable(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)

    def _on_remove(self, day: int, meal_type: str) -> None:
        cell = self._cells.get((day, meal_type))
        if cell:
            cell.clear()
            self.slot_changed.emit(day, meal_type, None, 0.0)

    def set_slot(
        self,
        day: int,
        meal_type: str,
        recipe_id: object,
        recipe_name: str,
        servings: float,
    ) -> None:
        cell = self._cells.get((day, meal_type))
        if cell:
            cell.set_recipe(recipe_id, recipe_name, servings)

    def clear_all(self) -> None:
        for cell in self._cells.values():
            cell.clear()

    def get_slots(self) -> list[tuple[int, str, object, float]]:
        """Возвращает заполненные слоты: [(day, meal_type, recipe_id, servings)]."""
        return [
            (day, mt, cell.recipe_id, cell.servings)
            for (day, mt), cell in self._cells.items()
            if cell.recipe_id is not None
        ]
