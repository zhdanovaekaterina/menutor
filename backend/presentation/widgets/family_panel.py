"""Family member management panel."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from backend.application.use_cases.manage_family import FamilyMemberData
from backend.domain.entities.family_member import FamilyMember


class FamilyPanel(QWidget):
    """Панель управления членами семьи."""

    create_member_requested = Signal(FamilyMemberData)
    edit_member_requested = Signal(object, FamilyMemberData)
    delete_member_requested = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._selected_member: FamilyMember | None = None
        self._members: list[FamilyMember] = []

        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(
            ["Имя", "Коэф. порции", "Ограничения", "Комментарий"]
        )
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.selectionModel().currentRowChanged.connect(self._on_row_selected)

        # Form
        self._name_edit = QLineEdit()
        self._multiplier_spin = QDoubleSpinBox()
        self._multiplier_spin.setMinimum(0.1)
        self._multiplier_spin.setMaximum(5.0)
        self._multiplier_spin.setDecimals(1)
        self._multiplier_spin.setSingleStep(0.1)
        self._multiplier_spin.setValue(1.0)
        self._restrictions_edit = QLineEdit()
        self._comment_edit = QLineEdit()

        form = QFormLayout()
        form.addRow("Имя:*", self._name_edit)
        form.addRow("Коэф. порции:", self._multiplier_spin)
        form.addRow("Ограничения:", self._restrictions_edit)
        form.addRow("Комментарий:", self._comment_edit)

        btns = QHBoxLayout()
        self._save_btn = QPushButton("Сохранить")
        self._delete_btn = QPushButton("Удалить")
        self._clear_btn = QPushButton("Очистить")
        self._save_btn.clicked.connect(self._on_save)
        self._delete_btn.clicked.connect(self._on_delete)
        self._clear_btn.clicked.connect(self._clear_form)
        btns.addWidget(self._save_btn)
        btns.addWidget(self._delete_btn)
        btns.addWidget(self._clear_btn)

        form_box = QGroupBox("Добавить / редактировать")
        form_layout = QVBoxLayout(form_box)
        form_layout.addLayout(form)
        form_layout.addLayout(btns)

        layout = QVBoxLayout(self)
        layout.addWidget(self._table)
        layout.addWidget(form_box)

    def set_members(self, members: list[FamilyMember]) -> None:
        self._members = members
        self._table.setRowCount(0)
        for m in members:
            row = self._table.rowCount()
            self._table.insertRow(row)
            self._table.setItem(row, 0, QTableWidgetItem(m.name))
            self._table.setItem(row, 1, QTableWidgetItem(str(m.portion_multiplier)))
            self._table.setItem(row, 2, QTableWidgetItem(m.dietary_restrictions))
            self._table.setItem(row, 3, QTableWidgetItem(m.comment))

    def _on_row_selected(self, current, _previous) -> None:
        row = current.row()
        if 0 <= row < len(self._members):
            self._selected_member = self._members[row]
            m = self._selected_member
            self._name_edit.setText(m.name)
            self._multiplier_spin.setValue(m.portion_multiplier)
            self._restrictions_edit.setText(m.dietary_restrictions)
            self._comment_edit.setText(m.comment)

    def _on_save(self) -> None:
        name = self._name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите имя члена семьи.")
            return
        data = FamilyMemberData(
            name=name,
            portion_multiplier=self._multiplier_spin.value(),
            dietary_restrictions=self._restrictions_edit.text().strip(),
            comment=self._comment_edit.text().strip(),
        )
        if self._selected_member is not None:
            self.edit_member_requested.emit(self._selected_member.id, data)
        else:
            self.create_member_requested.emit(data)

    def _on_delete(self) -> None:
        if self._selected_member is None:
            QMessageBox.information(self, "Удаление", "Выберите члена семьи для удаления.")
            return
        reply = QMessageBox.question(
            self, "Подтверждение", f"Удалить «{self._selected_member.name}»?"
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_member_requested.emit(self._selected_member.id)
            self._selected_member = None
            self._clear_form()

    def _clear_form(self) -> None:
        self._selected_member = None
        self._name_edit.clear()
        self._multiplier_spin.setValue(1.0)
        self._restrictions_edit.clear()
        self._comment_edit.clear()
