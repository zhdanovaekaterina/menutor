"""Tests for SettingsView — navigation, delegation to panels, public API."""

from unittest.mock import MagicMock

from PySide6.QtWidgets import QApplication

from src.application.use_cases.manage_family import FamilyMemberData
from src.domain.entities.family_member import FamilyMember
from src.domain.value_objects.category import Category
from src.domain.value_objects.types import FamilyMemberId
from src.presentation.views.settings_view import SettingsView


def _members() -> list[FamilyMember]:
    return [
        FamilyMember(FamilyMemberId(1), "Папа"),
        FamilyMember(FamilyMemberId(2), "Мама"),
    ]


def _categories() -> list[Category]:
    return [
        Category(1, "Бакалея", True),
        Category(2, "Молочные", False),
    ]


class TestSettingsViewNavigation:
    def test_initial_page_is_family(self, qapp: QApplication) -> None:
        view = SettingsView()
        assert view._stack.currentIndex() == 0
        assert view._stack.currentWidget() is view.family_panel

    def test_nav_to_product_categories(self, qapp: QApplication) -> None:
        view = SettingsView()
        view._nav.setCurrentRow(1)
        assert view._stack.currentWidget() is view.product_cat_panel

    def test_nav_to_recipe_categories(self, qapp: QApplication) -> None:
        view = SettingsView()
        view._nav.setCurrentRow(2)
        assert view._stack.currentWidget() is view.recipe_cat_panel

    def test_nav_to_import_export(self, qapp: QApplication) -> None:
        view = SettingsView()
        view._nav.setCurrentRow(3)
        assert view._stack.currentWidget() is view.ie_panel

    def test_nav_has_four_items(self, qapp: QApplication) -> None:
        view = SettingsView()
        assert view._nav.count() == 4


class TestSettingsViewDelegation:
    def test_set_family_members_delegates_to_panel(self, qapp: QApplication) -> None:
        view = SettingsView()
        view.set_family_members(_members())
        assert view.family_panel._table.rowCount() == 2

    def test_set_product_categories_delegates_to_panel(self, qapp: QApplication) -> None:
        view = SettingsView()
        view.set_product_categories(_categories())
        assert view.product_cat_panel._table.rowCount() == 2

    def test_set_recipe_categories_delegates_to_panel(self, qapp: QApplication) -> None:
        view = SettingsView()
        view.set_recipe_categories(_categories())
        assert view.recipe_cat_panel._table.rowCount() == 2


class TestSettingsViewSignalWiring:
    def test_family_create_signal_propagates(self, qapp: QApplication) -> None:
        view = SettingsView()
        spy = MagicMock()
        view.create_member_requested.connect(spy)

        data = FamilyMemberData(name="Тест")
        view.family_panel.create_member_requested.emit(data)

        spy.assert_called_once_with(data)

    def test_export_text_signal_propagates(self, qapp: QApplication) -> None:
        view = SettingsView()
        spy = MagicMock()
        view.export_text_requested.connect(spy)

        view.ie_panel.export_text_requested.emit()

        spy.assert_called_once()
