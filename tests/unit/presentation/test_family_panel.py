"""Tests for FamilyPanel widget — member display, form, signal emission."""

from unittest.mock import MagicMock, patch

from PySide6.QtWidgets import QApplication

from backend.application.use_cases.manage_family import FamilyMemberData
from backend.domain.entities.family_member import FamilyMember
from backend.domain.value_objects.types import FamilyMemberId
from backend.presentation.widgets.family_panel import FamilyPanel


def _members() -> list[FamilyMember]:
    return [
        FamilyMember(FamilyMemberId(1), "Папа", portion_multiplier=1.0,
                     dietary_restrictions="нет глютена", comment=""),
        FamilyMember(FamilyMemberId(2), "Мама", portion_multiplier=1.0),
        FamilyMember(FamilyMemberId(3), "Ребёнок", portion_multiplier=0.5,
                     comment="маленький"),
    ]


class TestFamilyPanelSetMembers:
    def test_sets_table_rows(self, qapp: QApplication) -> None:
        panel = FamilyPanel()
        panel.set_members(_members())
        assert panel._table.rowCount() == 3

    def test_displays_name(self, qapp: QApplication) -> None:
        panel = FamilyPanel()
        panel.set_members(_members())
        assert panel._table.item(0, 0).text() == "Папа"

    def test_displays_multiplier(self, qapp: QApplication) -> None:
        panel = FamilyPanel()
        panel.set_members(_members())
        assert panel._table.item(2, 1).text() == "0.5"

    def test_displays_restrictions(self, qapp: QApplication) -> None:
        panel = FamilyPanel()
        panel.set_members(_members())
        assert panel._table.item(0, 2).text() == "нет глютена"

    def test_displays_comment(self, qapp: QApplication) -> None:
        panel = FamilyPanel()
        panel.set_members(_members())
        assert panel._table.item(2, 3).text() == "маленький"

    def test_replaces_previous_data(self, qapp: QApplication) -> None:
        panel = FamilyPanel()
        panel.set_members(_members())
        panel.set_members([FamilyMember(FamilyMemberId(1), "Один")])
        assert panel._table.rowCount() == 1


class TestFamilyPanelRowSelection:
    def test_selecting_row_populates_form(self, qapp: QApplication) -> None:
        panel = FamilyPanel()
        panel.set_members(_members())
        panel._table.setCurrentCell(0, 0)

        assert panel._name_edit.text() == "Папа"
        assert panel._multiplier_spin.value() == 1.0
        assert panel._restrictions_edit.text() == "нет глютена"

    def test_selecting_different_row_updates_form(self, qapp: QApplication) -> None:
        panel = FamilyPanel()
        panel.set_members(_members())

        panel._table.setCurrentCell(2, 0)
        assert panel._name_edit.text() == "Ребёнок"
        assert panel._multiplier_spin.value() == 0.5
        assert panel._comment_edit.text() == "маленький"


class TestFamilyPanelSave:
    def test_save_new_emits_create(self, qapp: QApplication) -> None:
        panel = FamilyPanel()
        spy = MagicMock()
        panel.create_member_requested.connect(spy)

        panel._name_edit.setText("Новый")
        panel._multiplier_spin.setValue(0.8)
        panel._restrictions_edit.setText("без лактозы")
        panel._comment_edit.setText("комментарий")
        panel._on_save()

        spy.assert_called_once()
        data: FamilyMemberData = spy.call_args[0][0]
        assert data.name == "Новый"
        assert data.portion_multiplier == 0.8
        assert data.dietary_restrictions == "без лактозы"
        assert data.comment == "комментарий"

    def test_save_existing_emits_edit(self, qapp: QApplication) -> None:
        panel = FamilyPanel()
        panel.set_members(_members())
        spy = MagicMock()
        panel.edit_member_requested.connect(spy)

        panel._table.setCurrentCell(0, 0)
        panel._name_edit.setText("Папа (обновлён)")
        panel._on_save()

        spy.assert_called_once()
        member_id = spy.call_args[0][0]
        data: FamilyMemberData = spy.call_args[0][1]
        assert member_id == FamilyMemberId(1)
        assert data.name == "Папа (обновлён)"

    @patch("backend.presentation.widgets.family_panel.QMessageBox.warning")
    def test_save_empty_name_does_not_emit(
        self, mock_warning: MagicMock, qapp: QApplication,
    ) -> None:
        panel = FamilyPanel()
        create_spy = MagicMock()
        edit_spy = MagicMock()
        panel.create_member_requested.connect(create_spy)
        panel.edit_member_requested.connect(edit_spy)

        panel._name_edit.setText("")
        panel._on_save()

        create_spy.assert_not_called()
        edit_spy.assert_not_called()
        mock_warning.assert_called_once()


class TestFamilyPanelClear:
    def test_clear_resets_form(self, qapp: QApplication) -> None:
        panel = FamilyPanel()
        panel.set_members(_members())
        panel._table.setCurrentCell(0, 0)

        panel._clear_form()

        assert panel._name_edit.text() == ""
        assert panel._multiplier_spin.value() == 1.0
        assert panel._restrictions_edit.text() == ""
        assert panel._comment_edit.text() == ""
        assert panel._selected_member is None
