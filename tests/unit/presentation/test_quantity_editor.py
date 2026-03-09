"""Tests for QuantityEditor widget — value get/set, signal emission, unit management."""

from unittest.mock import MagicMock

from PySide6.QtWidgets import QApplication

from src.presentation.widgets.quantity_editor import QuantityEditor


class TestQuantityEditorInit:
    def test_default_amount(self, qapp: QApplication) -> None:
        editor = QuantityEditor()
        assert editor.get_amount() == 0.01  # minimum

    def test_default_unit_is_first_option(self, qapp: QApplication) -> None:
        editor = QuantityEditor()
        assert editor.get_unit() == "г"


class TestQuantityEditorGetSet:
    def test_set_value(self, qapp: QApplication) -> None:
        editor = QuantityEditor()
        editor.set_value(500.0, "кг")
        assert editor.get_amount() == 500.0
        assert editor.get_unit() == "кг"

    def test_set_value_unknown_unit_stays_at_current(self, qapp: QApplication) -> None:
        editor = QuantityEditor()
        editor.set_value(100.0, "nonexistent")
        assert editor.get_amount() == 100.0
        # unit stays at previous value since "nonexistent" is not found
        assert editor.get_unit() == "г"

    def test_set_value_does_not_emit_signal(self, qapp: QApplication) -> None:
        editor = QuantityEditor()
        spy = MagicMock()
        editor.value_changed.connect(spy)

        editor.set_value(200.0, "мл")

        spy.assert_not_called()


class TestQuantityEditorSignals:
    def test_changing_amount_emits_signal(self, qapp: QApplication) -> None:
        editor = QuantityEditor()
        spy = MagicMock()
        editor.value_changed.connect(spy)

        editor._spin.setValue(42.0)

        spy.assert_called()
        amount, unit = spy.call_args[0]
        assert amount == 42.0
        assert unit == "г"

    def test_changing_unit_emits_signal(self, qapp: QApplication) -> None:
        editor = QuantityEditor()
        spy = MagicMock()
        editor.value_changed.connect(spy)

        editor._unit_combo.setCurrentText("кг")

        spy.assert_called()
        _, unit = spy.call_args[0]
        assert unit == "кг"


class TestQuantityEditorSetUnits:
    def test_set_units_replaces_options(self, qapp: QApplication) -> None:
        editor = QuantityEditor()
        editor.set_units(["мл", "л"])
        assert editor._unit_combo.count() == 2
        assert editor.get_unit() == "мл"

    def test_set_units_preserves_current_if_present(self, qapp: QApplication) -> None:
        editor = QuantityEditor()
        editor.set_value(1.0, "кг")
        editor.set_units(["г", "кг", "мл"])
        assert editor.get_unit() == "кг"

    def test_set_units_resets_to_first_if_current_gone(self, qapp: QApplication) -> None:
        editor = QuantityEditor()
        editor.set_value(1.0, "кг")
        editor.set_units(["мл", "л"])
        assert editor.get_unit() == "мл"

    def test_set_units_does_not_emit_signal(self, qapp: QApplication) -> None:
        editor = QuantityEditor()
        spy = MagicMock()
        editor.value_changed.connect(spy)

        editor.set_units(["мл", "л"])

        spy.assert_not_called()
