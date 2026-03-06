from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QDoubleSpinBox, QHBoxLayout, QWidget

from src.presentation.units import UNIT_DISPLAY_OPTIONS


class QuantityEditor(QWidget):
    """Виджет ввода количества: числовое поле + выбор единицы измерения."""

    value_changed = Signal(float, str)  # amount, unit

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._spin = QDoubleSpinBox()
        self._spin.setMinimum(0.01)
        self._spin.setMaximum(99999.0)
        self._spin.setDecimals(2)
        self._spin.setSingleStep(1.0)

        self._unit_combo = QComboBox()
        self._unit_combo.addItems(UNIT_DISPLAY_OPTIONS)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._spin)
        layout.addWidget(self._unit_combo)

        self._spin.valueChanged.connect(self._emit_change)
        self._unit_combo.currentTextChanged.connect(self._emit_change)

    def _emit_change(self, _=None) -> None:
        self.value_changed.emit(self._spin.value(), self._unit_combo.currentText())

    def get_amount(self) -> float:
        return self._spin.value()

    def get_unit(self) -> str:
        return self._unit_combo.currentText()

    def set_value(self, amount: float, unit: str) -> None:
        self._spin.blockSignals(True)
        self._unit_combo.blockSignals(True)
        self._spin.setValue(amount)
        idx = self._unit_combo.findText(unit)
        if idx >= 0:
            self._unit_combo.setCurrentIndex(idx)
        self._spin.blockSignals(False)
        self._unit_combo.blockSignals(False)

    def set_units(self, units: list[str]) -> None:
        """Заменяет список доступных единиц."""
        current = self._unit_combo.currentText()
        self._unit_combo.blockSignals(True)
        self._unit_combo.clear()
        self._unit_combo.addItems(units)
        idx = self._unit_combo.findText(current)
        self._unit_combo.setCurrentIndex(max(idx, 0))
        self._unit_combo.blockSignals(False)
