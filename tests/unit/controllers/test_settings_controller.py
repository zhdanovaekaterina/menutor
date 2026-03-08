"""Unit tests for SettingsController — family members, categories, export."""

from unittest.mock import MagicMock

import pytest

from src.application.use_cases.manage_family import FamilyMemberData
from src.domain.entities.family_member import FamilyMember
from src.domain.entities.shopping_list import ShoppingList
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
def export_uc() -> dict[str, MagicMock]:
    return {"text": MagicMock(), "csv": MagicMock()}


@pytest.fixture
def product_cat_uc() -> dict[str, MagicMock]:
    return {
        "list": MagicMock(), "create": MagicMock(),
        "edit": MagicMock(), "delete": MagicMock(), "check": MagicMock(),
    }


@pytest.fixture
def recipe_cat_uc() -> dict[str, MagicMock]:
    return {
        "list": MagicMock(), "create": MagicMock(),
        "edit": MagicMock(), "delete": MagicMock(), "check": MagicMock(),
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
    export_uc: dict[str, MagicMock],
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
        export_text_uc=export_uc["text"],
        export_csv_uc=export_uc["csv"],
        list_product_categories_uc=product_cat_uc["list"],
        create_product_category_uc=product_cat_uc["create"],
        edit_product_category_uc=product_cat_uc["edit"],
        delete_product_category_uc=product_cat_uc["delete"],
        check_product_category_used_uc=product_cat_uc["check"],
        list_recipe_categories_uc=recipe_cat_uc["list"],
        create_recipe_category_uc=recipe_cat_uc["create"],
        edit_recipe_category_uc=recipe_cat_uc["edit"],
        delete_recipe_category_uc=recipe_cat_uc["delete"],
        check_recipe_category_used_uc=recipe_cat_uc["check"],
    )


class TestSettingsControllerInit:
    def test_connects_all_signals(self, view: MagicMock, controller: SettingsController) -> None:
        view.create_member_requested.connect.assert_called_once()
        view.edit_member_requested.connect.assert_called_once()
        view.delete_member_requested.connect.assert_called_once()
        view.export_text_requested.connect.assert_called_once()
        view.export_csv_requested.connect.assert_called_once()
        view.create_product_category_requested.connect.assert_called_once()
        view.edit_product_category_requested.connect.assert_called_once()
        view.delete_product_category_requested.connect.assert_called_once()
        view.create_recipe_category_requested.connect.assert_called_once()
        view.edit_recipe_category_requested.connect.assert_called_once()
        view.delete_recipe_category_requested.connect.assert_called_once()

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
        members_uc["create"].execute.side_effect = ValueError("Имя пустое")
        data = FamilyMemberData(name="")
        controller._on_create(data)
        view.show_error.assert_called_with("Имя пустое")


class TestSettingsControllerProductCategories:
    def test_create_product_category(
        self, product_cat_uc: dict[str, MagicMock], controller: SettingsController,
    ) -> None:
        controller._on_create_product_cat("Овощи")
        product_cat_uc["create"].execute.assert_called_once_with("Овощи")

    def test_edit_product_category(
        self, product_cat_uc: dict[str, MagicMock], controller: SettingsController,
    ) -> None:
        controller._on_edit_product_cat(1, "Бакалея (ред.)")
        product_cat_uc["edit"].execute.assert_called_once_with(1, "Бакалея (ред.)")

    def test_delete_product_category(
        self, product_cat_uc: dict[str, MagicMock], controller: SettingsController,
    ) -> None:
        controller._on_delete_product_cat(1)
        product_cat_uc["delete"].execute.assert_called_once_with(1)

    def test_create_error_shows_message(
        self,
        product_cat_uc: dict[str, MagicMock],
        view: MagicMock,
        controller: SettingsController,
    ) -> None:
        product_cat_uc["create"].execute.side_effect = ValueError("Duplicate")
        controller._on_create_product_cat("Бакалея")
        view.show_error.assert_called_with("Duplicate")


class TestSettingsControllerRecipeCategories:
    def test_create_recipe_category(
        self, recipe_cat_uc: dict[str, MagicMock], controller: SettingsController,
    ) -> None:
        controller._on_create_recipe_cat("Десерты")
        recipe_cat_uc["create"].execute.assert_called_once_with("Десерты")

    def test_edit_recipe_category(
        self, recipe_cat_uc: dict[str, MagicMock], controller: SettingsController,
    ) -> None:
        controller._on_edit_recipe_cat(1, "Завтраки (ред.)")
        recipe_cat_uc["edit"].execute.assert_called_once_with(1, "Завтраки (ред.)")

    def test_delete_recipe_category(
        self, recipe_cat_uc: dict[str, MagicMock], controller: SettingsController,
    ) -> None:
        controller._on_delete_recipe_cat(1)
        recipe_cat_uc["delete"].execute.assert_called_once_with(1)


class TestSettingsControllerExport:
    def test_export_text_without_shopping_list_shows_error(
        self, view: MagicMock, controller: SettingsController,
    ) -> None:
        view.show_error.reset_mock()
        controller._on_export_text()
        view.show_error.assert_called_once_with("Сначала сформируйте список покупок.")

    def test_export_csv_without_shopping_list_shows_error(
        self, view: MagicMock, controller: SettingsController,
    ) -> None:
        view.show_error.reset_mock()
        controller._on_export_csv("/tmp/test.csv")
        view.show_error.assert_called_once_with("Сначала сформируйте список покупок.")

    def test_export_csv_delegates_to_use_case(
        self,
        export_uc: dict[str, MagicMock],
        controller: SettingsController,
    ) -> None:
        sl = ShoppingList()
        controller.set_shopping_list(sl)
        controller._on_export_csv("/tmp/out.csv")
        export_uc["csv"].execute.assert_called_once_with(sl, "/tmp/out.csv")
