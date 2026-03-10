"""Unit tests for SettingsController — family members and categories."""

from unittest.mock import MagicMock

import pytest

from src.application.use_cases.manage_family import FamilyMemberData
from src.domain.entities.family_member import FamilyMember
from src.domain.exceptions import EntityNotFoundError
from src.domain.value_objects.types import FamilyMemberId
from src.presentation.controllers.settings_controller import SettingsController


@pytest.fixture
def view() -> MagicMock:
    return MagicMock()


@pytest.fixture
def members_uc() -> dict[str, MagicMock]:
    return {
        "create": MagicMock(),
        "edit": MagicMock(),
        "delete": MagicMock(),
        "list": MagicMock(),
    }


@pytest.fixture
def product_cat_uc() -> dict[str, MagicMock]:
    return {
        "list": MagicMock(), "create": MagicMock(),
        "edit": MagicMock(), "delete": MagicMock(),
        "hard_delete": MagicMock(), "activate": MagicMock(),
        "check": MagicMock(),
    }


@pytest.fixture
def recipe_cat_uc() -> dict[str, MagicMock]:
    return {
        "list": MagicMock(), "create": MagicMock(),
        "edit": MagicMock(), "delete": MagicMock(),
        "hard_delete": MagicMock(), "activate": MagicMock(),
        "check": MagicMock(),
    }


@pytest.fixture
def sample_members() -> list[FamilyMember]:
    return [
        FamilyMember(id=FamilyMemberId(1), name="Папа", portion_multiplier=1.0),
        FamilyMember(id=FamilyMemberId(2), name="Ребёнок", portion_multiplier=0.5),
    ]


@pytest.fixture
def controller(
    view: MagicMock,
    members_uc: dict[str, MagicMock],
    product_cat_uc: dict[str, MagicMock],
    recipe_cat_uc: dict[str, MagicMock],
    sample_members: list[FamilyMember],
) -> SettingsController:
    members_uc["list"].execute.return_value = sample_members
    product_cat_uc["list"].execute.return_value = [(1, "Бакалея", True)]
    recipe_cat_uc["list"].execute.return_value = [(1, "Завтраки", True)]
    return SettingsController(
        view=view,
        create_member_uc=members_uc["create"],
        edit_member_uc=members_uc["edit"],
        delete_member_uc=members_uc["delete"],
        list_members_uc=members_uc["list"],
        list_product_categories_uc=product_cat_uc["list"],
        create_product_category_uc=product_cat_uc["create"],
        edit_product_category_uc=product_cat_uc["edit"],
        delete_product_category_uc=product_cat_uc["delete"],
        hard_delete_product_category_uc=product_cat_uc["hard_delete"],
        activate_product_category_uc=product_cat_uc["activate"],
        check_product_category_used_uc=product_cat_uc["check"],
        list_recipe_categories_uc=recipe_cat_uc["list"],
        create_recipe_category_uc=recipe_cat_uc["create"],
        edit_recipe_category_uc=recipe_cat_uc["edit"],
        delete_recipe_category_uc=recipe_cat_uc["delete"],
        hard_delete_recipe_category_uc=recipe_cat_uc["hard_delete"],
        activate_recipe_category_uc=recipe_cat_uc["activate"],
        check_recipe_category_used_uc=recipe_cat_uc["check"],
    )


class TestSettingsControllerInit:
    def test_connects_family_signals(
        self, view: MagicMock, controller: SettingsController,
    ) -> None:
        view.create_member_requested.connect.assert_called_once()
        view.edit_member_requested.connect.assert_called_once()
        view.delete_member_requested.connect.assert_called_once()

    def test_connects_category_panel_signals(
        self, view: MagicMock, controller: SettingsController,
    ) -> None:
        view.product_cat_panel.create_requested.connect.assert_called_once()
        view.product_cat_panel.edit_requested.connect.assert_called_once()
        view.product_cat_panel.delete_requested.connect.assert_called_once()
        view.product_cat_panel.activate_requested.connect.assert_called_once()
        view.recipe_cat_panel.create_requested.connect.assert_called_once()
        view.recipe_cat_panel.edit_requested.connect.assert_called_once()
        view.recipe_cat_panel.delete_requested.connect.assert_called_once()
        view.recipe_cat_panel.activate_requested.connect.assert_called_once()

    def test_loads_data_on_init(
        self,
        view: MagicMock,
        sample_members: list[FamilyMember],
        controller: SettingsController,
    ) -> None:
        view.set_family_members.assert_called_once_with(sample_members)
        view.set_product_categories.assert_called_once()
        view.set_recipe_categories.assert_called_once()


class TestSettingsControllerFamily:
    def test_create_member(
        self, members_uc: dict[str, MagicMock], controller: SettingsController,
    ) -> None:
        data = FamilyMemberData(name="Бабушка", portion_multiplier=0.8)
        controller._on_create(data)
        members_uc["create"].execute.assert_called_once_with(data)

    def test_edit_member(
        self, members_uc: dict[str, MagicMock], controller: SettingsController,
    ) -> None:
        data = FamilyMemberData(name="Папа (ред.)", portion_multiplier=1.2)
        controller._on_edit(1, data)
        members_uc["edit"].execute.assert_called_once_with(FamilyMemberId(1), data)

    def test_delete_member(
        self, members_uc: dict[str, MagicMock], controller: SettingsController,
    ) -> None:
        controller._on_delete(1)
        members_uc["delete"].execute.assert_called_once_with(FamilyMemberId(1))

    def test_create_member_error(
        self,
        members_uc: dict[str, MagicMock],
        view: MagicMock,
        controller: SettingsController,
    ) -> None:
        members_uc["create"].execute.side_effect = EntityNotFoundError("Имя пустое")
        data = FamilyMemberData(name="")
        controller._on_create(data)
        view.show_error.assert_called_with("Имя пустое")


class TestSettingsControllerProductCategories:
    def test_create_product_category(
        self, product_cat_uc: dict[str, MagicMock], controller: SettingsController,
    ) -> None:
        controller._product_cat_handler._on_create("Овощи")
        product_cat_uc["create"].execute.assert_called_once_with("Овощи")

    def test_edit_product_category(
        self, product_cat_uc: dict[str, MagicMock], controller: SettingsController,
    ) -> None:
        controller._product_cat_handler._on_edit(1, "Бакалея (ред.)")
        product_cat_uc["edit"].execute.assert_called_once_with(1, "Бакалея (ред.)")

    def test_delete_unused_product_category_hard_deletes(
        self, product_cat_uc: dict[str, MagicMock], controller: SettingsController,
    ) -> None:
        product_cat_uc["check"].execute.return_value = False
        controller._product_cat_handler._on_delete(1)
        product_cat_uc["hard_delete"].execute.assert_called_once_with(1)
        product_cat_uc["delete"].execute.assert_not_called()

    def test_create_error_shows_message(
        self,
        product_cat_uc: dict[str, MagicMock],
        view: MagicMock,
        controller: SettingsController,
    ) -> None:
        product_cat_uc["create"].execute.side_effect = EntityNotFoundError("Duplicate")
        controller._product_cat_handler._on_create("Бакалея")
        view.show_error.assert_called_with("Duplicate")


class TestSettingsControllerRecipeCategories:
    def test_create_recipe_category(
        self, recipe_cat_uc: dict[str, MagicMock], controller: SettingsController,
    ) -> None:
        controller._recipe_cat_handler._on_create("Десерты")
        recipe_cat_uc["create"].execute.assert_called_once_with("Десерты")

    def test_edit_recipe_category(
        self, recipe_cat_uc: dict[str, MagicMock], controller: SettingsController,
    ) -> None:
        controller._recipe_cat_handler._on_edit(1, "Завтраки (ред.)")
        recipe_cat_uc["edit"].execute.assert_called_once_with(1, "Завтраки (ред.)")

    def test_delete_unused_recipe_category_hard_deletes(
        self, recipe_cat_uc: dict[str, MagicMock], controller: SettingsController,
    ) -> None:
        recipe_cat_uc["check"].execute.return_value = False
        controller._recipe_cat_handler._on_delete(1)
        recipe_cat_uc["hard_delete"].execute.assert_called_once_with(1)
        recipe_cat_uc["delete"].execute.assert_not_called()


class TestSettingsControllerActivateCategory:
    def test_activate_product_category(
        self, product_cat_uc: dict[str, MagicMock], controller: SettingsController,
    ) -> None:
        controller._product_cat_handler._on_activate(1)
        product_cat_uc["activate"].execute.assert_called_once_with(1)

    def test_activate_recipe_category(
        self, recipe_cat_uc: dict[str, MagicMock], controller: SettingsController,
    ) -> None:
        controller._recipe_cat_handler._on_activate(1)
        recipe_cat_uc["activate"].execute.assert_called_once_with(1)
