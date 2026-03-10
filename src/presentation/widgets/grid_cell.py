"""Grid cell widget for the menu planner drag-drop grid."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.presentation.units import to_display

MIME_RECIPE = "application/x-menutor-recipe-id"
MIME_PRODUCT = "application/x-menutor-product-id"


_ITEM_STYLE = {
    "recipe": (
        "background-color: #e8f0fe; border: 1px solid #a4c2f4;"
        " border-radius: 4px; padding: 2px 4px;"
    ),
    "product": (
        "background-color: #fef3e0; border: 1px solid #f4bc78;"
        " border-radius: 4px; padding: 2px 4px;"
    ),
}

_LABEL_STYLE = {
    "recipe": "color: #1a56db;",
    "product": "color: #b45309;",
}


class ItemRow(QFrame):
    """Single item display inside a grid cell, with a remove button."""

    remove_clicked = Signal()
    edit_clicked = Signal()

    def __init__(
        self,
        label_text: str,
        item_type: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        style = _ITEM_STYLE.get(item_type, "")
        if style:
            self.setStyleSheet(style)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        self._label = QLabel(label_text)
        self._label.setWordWrap(True)
        self._label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        label_style = _LABEL_STYLE.get(item_type, "")
        if label_style:
            self._label.setStyleSheet(label_style)
        self._label.setToolTip("Двойной клик — изменить количество")

        self._remove_btn = QPushButton("✕")
        self._remove_btn.setMaximumSize(18, 18)
        self._remove_btn.clicked.connect(self.remove_clicked)

        layout.addWidget(self._label, 1)
        layout.addWidget(self._remove_btn)

    def mouseDoubleClickEvent(self, event) -> None:  # type: ignore[override]
        self.edit_clicked.emit()


class GridCell(QFrame):
    """Одна ячейка сетки меню. Принимает drag рецептов и продуктов."""

    item_added = Signal(int, str, str, int, float, str)  # day, meal_type, item_type, item_id, servings_or_qty, unit
    item_removed = Signal(int, str, str, int)  # day, meal_type, item_type, item_id

    def __init__(
        self,
        day: int,
        meal_type: str,
        product_units: dict,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.day = day
        self.meal_type = meal_type
        self._product_units = product_units
        self._default_servings: float = 1.0
        self._items: list[dict] = []

        self.setAcceptDrops(True)
        self.setFrameShape(QFrame.Shape.Box)
        self.setMinimumSize(110, 70)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(4, 4, 4, 4)
        self._layout.setSpacing(2)

    def _rebuild_ui(self) -> None:
        while self._layout.count():
            child = self._layout.takeAt(0)
            if child is not None and child.widget() is not None:
                child.widget().deleteLater()  # type: ignore[union-attr]

        for item in self._items:
            if item["type"] == "recipe":
                text = f"{item['name']} ({item['servings']:.1f} п.)"
            else:
                text = f"{item['name']} ({item['quantity']:.1f} {to_display(item['unit'])})"

            row = ItemRow(text, item_type=item["type"])
            item_type = item["type"]
            item_id = item["id"]
            row.remove_clicked.connect(
                lambda _it=item_type, _iid=item_id: self.item_removed.emit(
                    self.day, self.meal_type, _it, _iid
                )
            )
            row.edit_clicked.connect(
                lambda _it=item_type, _iid=item_id: self._edit_item(_it, _iid)
            )
            self._layout.addWidget(row)

    def dragEnterEvent(self, event) -> None:  # type: ignore[override]
        md = event.mimeData()
        if md.hasFormat(MIME_RECIPE) or md.hasFormat(MIME_PRODUCT):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:  # type: ignore[override]
        md = event.mimeData()
        if md.hasFormat(MIME_RECIPE) or md.hasFormat(MIME_PRODUCT):
            event.acceptProposedAction()
        else:
            event.ignore()

    def _find_item(self, item_type: str, item_id: int) -> dict | None:
        for it in self._items:
            if it["type"] == item_type and it["id"] == item_id:
                return it
        return None

    def _ask_merge(self, display_name: str) -> bool:
        reply = QMessageBox.question(
            self,
            "Элемент уже добавлен",
            f"«{display_name}» уже есть в этой ячейке.\n"
            "Добавить количество к существующему?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        return reply == QMessageBox.StandardButton.Yes

    def _edit_item(self, item_type: str, item_id: int) -> None:
        item = self._find_item(item_type, item_id)
        if item is None:
            return

        if item_type == "recipe":
            new_val, ok = QInputDialog.getDouble(
                self, "Порции",
                f"Количество порций для «{item['name']}»:",
                item["servings"], 0.5, 99999.0, 1,
            )
            if not ok:
                return
            item["servings"] = new_val
            self._rebuild_ui()
            self.item_added.emit(
                self.day, self.meal_type, "recipe", item_id, new_val, ""
            )
        else:
            new_qty, ok = QInputDialog.getDouble(
                self, "Количество",
                f"Количество для «{item['name']}» ({to_display(item['unit'])}):",
                item["quantity"], 0.01, 99999.0, 2,
            )
            if not ok:
                return
            item["quantity"] = new_qty
            self._rebuild_ui()
            self.item_added.emit(
                self.day, self.meal_type, "product", item_id, new_qty, item["unit"]
            )

    def dropEvent(self, event) -> None:  # type: ignore[override]
        md = event.mimeData()
        if md.hasFormat(MIME_RECIPE):
            raw = md.data(MIME_RECIPE)
            recipe_id_val = int(raw.data().decode())
            display_name = md.text()

            existing = self._find_item("recipe", recipe_id_val)
            if existing is not None:
                if not self._ask_merge(display_name):
                    event.ignore()
                    return
                new_servings = existing["servings"] + self._default_servings
                existing["servings"] = new_servings
                self._rebuild_ui()
                event.acceptProposedAction()
                self.item_added.emit(
                    self.day, self.meal_type, "recipe", recipe_id_val, new_servings, ""
                )
            else:
                self.add_item("recipe", recipe_id_val, display_name, servings=self._default_servings)
                event.acceptProposedAction()
                self.item_added.emit(
                    self.day, self.meal_type, "recipe", recipe_id_val, self._default_servings, ""
                )
        elif md.hasFormat(MIME_PRODUCT):
            raw = md.data(MIME_PRODUCT)
            product_id_val = int(raw.data().decode())
            display_name = md.text()

            unit = self._product_units.get(product_id_val, "")
            unit_suffix = f" ({unit})" if unit else ""
            qty, ok = QInputDialog.getDouble(
                self, "Количество",
                f"Количество для «{display_name}»{unit_suffix}:",
                1.0, 0.01, 99999.0, 2,
            )
            if not ok:
                event.ignore()
                return

            existing = self._find_item("product", product_id_val)
            if existing is not None:
                if not self._ask_merge(display_name):
                    event.ignore()
                    return
                existing["quantity"] += qty
                existing["unit"] = unit
                new_qty = existing["quantity"]
                self._rebuild_ui()
                event.acceptProposedAction()
                self.item_added.emit(
                    self.day, self.meal_type, "product", product_id_val, new_qty, unit
                )
            else:
                self.add_item("product", product_id_val, display_name, quantity=qty, unit=unit)
                event.acceptProposedAction()
                self.item_added.emit(
                    self.day, self.meal_type, "product", product_id_val, qty, unit
                )
        else:
            event.ignore()

    def set_default_servings(self, n: float) -> None:
        self._default_servings = max(1.0, n)

    def add_item(
        self,
        item_type: str,
        item_id: int,
        name: str,
        servings: float = 1.0,
        quantity: float = 0.0,
        unit: str = "",
    ) -> None:
        self._items.append({
            "type": item_type,
            "id": item_id,
            "name": name,
            "servings": servings,
            "quantity": quantity,
            "unit": unit,
        })
        self._rebuild_ui()

    def update_item_name(self, item_type: str, item_id: int, new_name: str) -> None:
        """Обновить отображаемое имя элемента без удаления/пересоздания."""
        for it in self._items:
            if it["type"] == item_type and it["id"] == item_id:
                it["name"] = new_name
                self._rebuild_ui()
                return

    def remove_item(self, item_type: str, item_id: int) -> None:
        self._items = [
            it for it in self._items
            if not (it["type"] == item_type and it["id"] == item_id)
        ]
        self._rebuild_ui()

    def clear(self) -> None:
        self._items.clear()
        self._rebuild_ui()

    def get_items(self) -> list[dict]:
        return list(self._items)
