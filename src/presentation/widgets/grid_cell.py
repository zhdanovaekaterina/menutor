"""Grid cell widget for the menu planner drag-drop grid."""

import json

from PySide6.QtCore import QMimeData, Qt, Signal
from PySide6.QtGui import QDrag
from PySide6.QtWidgets import (
    QApplication,
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
MIME_SLOT_ITEM = "application/x-menutor-slot-item"


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
    """Single item display inside a grid cell, with remove button and drag support."""

    remove_clicked = Signal()
    edit_clicked = Signal()

    def __init__(
        self,
        label_text: str,
        item_type: str = "",
        item_data: dict | None = None,
        source_day: int | None = None,
        source_meal: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._item_data = item_data or {}
        self._source_day = source_day
        self._source_meal = source_meal
        self._drag_start_pos = None

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

        self.setCursor(Qt.CursorShape.OpenHandCursor)

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # type: ignore[override]
        if self._drag_start_pos is None:
            return
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        dist = (event.position().toPoint() - self._drag_start_pos).manhattanLength()
        if dist < QApplication.startDragDistance():
            return

        mime = QMimeData()
        payload = {
            **self._item_data,
            "source_day": self._source_day,
            "source_meal_type": self._source_meal,
        }
        mime.setData(MIME_SLOT_ITEM, json.dumps(payload).encode())

        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.exec(Qt.DropAction.MoveAction)

    def mouseReleaseEvent(self, event) -> None:  # type: ignore[override]
        self._drag_start_pos = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:  # type: ignore[override]
        self.edit_clicked.emit()


class GridCell(QFrame):
    """Одна ячейка сетки меню. Принимает drag рецептов, продуктов и перемещение элементов."""

    item_added = Signal(int, str, str, int, float, str)  # day, meal_type, item_type, item_id, servings_or_qty, unit
    item_removed = Signal(int, str, str, int)  # day, meal_type, item_type, item_id
    item_moved_from = Signal(int, str, str, int)  # source_day, source_meal_type, item_type, item_id

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

            row = ItemRow(
                text,
                item_type=item["type"],
                item_data=item,
                source_day=self.day,
                source_meal=self.meal_type,
            )
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

    # ------------------------------------------------------------------
    # Drag-and-drop
    # ------------------------------------------------------------------

    def _accepts_drag(self, event) -> bool:  # type: ignore[override]
        md = event.mimeData()
        return (
            md.hasFormat(MIME_RECIPE)
            or md.hasFormat(MIME_PRODUCT)
            or md.hasFormat(MIME_SLOT_ITEM)
        )

    def dragEnterEvent(self, event) -> None:  # type: ignore[override]
        if self._accepts_drag(event):
            event.acceptProposedAction()
            self.setLineWidth(2)
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:  # type: ignore[override]
        if self._accepts_drag(event):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event) -> None:  # type: ignore[override]
        self.setLineWidth(1)
        super().dragLeaveEvent(event)

    def dropEvent(self, event) -> None:  # type: ignore[override]
        self.setLineWidth(1)
        md = event.mimeData()

        if md.hasFormat(MIME_SLOT_ITEM):
            self._handle_slot_item_drop(event)
        elif md.hasFormat(MIME_RECIPE):
            self._handle_recipe_drop(event)
        elif md.hasFormat(MIME_PRODUCT):
            self._handle_product_drop(event)
        else:
            event.ignore()

    # ------------------------------------------------------------------
    # Drop handlers
    # ------------------------------------------------------------------

    def _handle_slot_item_drop(self, event) -> None:  # type: ignore[override]
        data = json.loads(event.mimeData().data(MIME_SLOT_ITEM).data().decode())
        source_day: int = data["source_day"]
        source_meal: str = data["source_meal_type"]
        item_type: str = data["type"]
        item_id: int = data["id"]
        drop_idx = self._drop_index(event.position().y())

        if source_day == self.day and source_meal == self.meal_type:
            # Reorder within same cell
            old_idx = next(
                (i for i, it in enumerate(self._items)
                 if it["type"] == item_type and it["id"] == item_id),
                None,
            )
            if old_idx is not None and old_idx != drop_idx:
                item = self._items.pop(old_idx)
                if drop_idx > old_idx:
                    drop_idx -= 1
                self._items.insert(drop_idx, item)
                self._rebuild_ui()
            event.acceptProposedAction()
        else:
            # Cross-cell move
            moved_item = {
                "type": item_type,
                "id": item_id,
                "name": data["name"],
                "servings": data.get("servings", 1.0),
                "quantity": data.get("quantity", 0.0),
                "unit": data.get("unit", ""),
            }

            existing = self._find_item(item_type, item_id)
            if existing is not None:
                if not self._ask_merge(data["name"]):
                    event.ignore()
                    return
                if item_type == "recipe":
                    existing["servings"] += moved_item["servings"]
                    self._rebuild_ui()
                    self.item_added.emit(
                        self.day, self.meal_type, "recipe", item_id,
                        existing["servings"], "",
                    )
                else:
                    existing["quantity"] += moved_item["quantity"]
                    existing["unit"] = moved_item["unit"]
                    self._rebuild_ui()
                    self.item_added.emit(
                        self.day, self.meal_type, "product", item_id,
                        existing["quantity"], existing["unit"],
                    )
            else:
                self._items.insert(drop_idx, moved_item)
                self._rebuild_ui()
                if item_type == "recipe":
                    self.item_added.emit(
                        self.day, self.meal_type, "recipe", item_id,
                        moved_item["servings"], "",
                    )
                else:
                    self.item_added.emit(
                        self.day, self.meal_type, "product", item_id,
                        moved_item["quantity"], moved_item["unit"],
                    )

            self.item_moved_from.emit(source_day, source_meal, item_type, item_id)
            event.acceptProposedAction()

    def _handle_recipe_drop(self, event) -> None:  # type: ignore[override]
        md = event.mimeData()
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

    def _handle_product_drop(self, event) -> None:  # type: ignore[override]
        md = event.mimeData()
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

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

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
                item["servings"], 0.1, 99999.0, 1,
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

    def _drop_index(self, y: float) -> int:
        """Calculate insertion index from drop y-coordinate."""
        for i in range(self._layout.count()):
            w = self._layout.itemAt(i).widget()
            if w is None:
                continue
            mid_y = w.y() + w.height() / 2
            if y < mid_y:
                return i
        return len(self._items)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

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
