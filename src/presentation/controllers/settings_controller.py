from typing import cast

from src.application.use_cases.import_export import (
    ExportShoppingListAsCsv,
    ExportShoppingListAsText,
)
from src.application.use_cases.manage_category import (
    CheckProductCategoryUsed,
    CheckRecipeCategoryUsed,
    CreateProductCategory,
    CreateRecipeCategory,
    DeleteProductCategory,
    DeleteRecipeCategory,
    EditProductCategory,
    EditRecipeCategory,
    ListAllProductCategories,
    ListAllRecipeCategories,
)
from src.application.use_cases.manage_family import (
    CreateFamilyMember,
    DeleteFamilyMember,
    EditFamilyMember,
    FamilyMemberData,
    ListFamilyMembers,
)
from src.domain.entities.shopping_list import ShoppingList
from src.domain.value_objects.types import FamilyMemberId
from src.presentation.views.settings_view import SettingsView


class SettingsController:
    """Соединяет SettingsView с use cases семьи, категорий и экспорта."""

    def __init__(
        self,
        view: SettingsView,
        create_member_uc: CreateFamilyMember,
        edit_member_uc: EditFamilyMember,
        delete_member_uc: DeleteFamilyMember,
        list_members_uc: ListFamilyMembers,
        export_text_uc: ExportShoppingListAsText,
        export_csv_uc: ExportShoppingListAsCsv,
        # Product categories
        list_product_categories_uc: ListAllProductCategories,
        create_product_category_uc: CreateProductCategory,
        edit_product_category_uc: EditProductCategory,
        delete_product_category_uc: DeleteProductCategory,
        check_product_category_used_uc: CheckProductCategoryUsed,
        # Recipe categories
        list_recipe_categories_uc: ListAllRecipeCategories,
        create_recipe_category_uc: CreateRecipeCategory,
        edit_recipe_category_uc: EditRecipeCategory,
        delete_recipe_category_uc: DeleteRecipeCategory,
        check_recipe_category_used_uc: CheckRecipeCategoryUsed,
    ) -> None:
        self._view = view
        self._create_uc = create_member_uc
        self._edit_uc = edit_member_uc
        self._delete_uc = delete_member_uc
        self._list_uc = list_members_uc
        self._export_text_uc = export_text_uc
        self._export_csv_uc = export_csv_uc
        self._last_shopping_list: ShoppingList | None = None

        # Product category use cases
        self._list_product_cat_uc = list_product_categories_uc
        self._create_product_cat_uc = create_product_category_uc
        self._edit_product_cat_uc = edit_product_category_uc
        self._delete_product_cat_uc = delete_product_category_uc
        self._check_product_cat_used_uc = check_product_category_used_uc

        # Recipe category use cases
        self._list_recipe_cat_uc = list_recipe_categories_uc
        self._create_recipe_cat_uc = create_recipe_category_uc
        self._edit_recipe_cat_uc = edit_recipe_category_uc
        self._delete_recipe_cat_uc = delete_recipe_category_uc
        self._check_recipe_cat_used_uc = check_recipe_category_used_uc

        # Family member signals
        view.create_member_requested.connect(self._on_create)
        view.edit_member_requested.connect(self._on_edit)
        view.delete_member_requested.connect(self._on_delete)

        # Export signals
        view.export_text_requested.connect(self._on_export_text)
        view.export_csv_requested.connect(self._on_export_csv)

        # Product category signals
        view.create_product_category_requested.connect(self._on_create_product_cat)
        view.edit_product_category_requested.connect(self._on_edit_product_cat)
        view.delete_product_category_requested.connect(self._on_delete_product_cat)

        # Recipe category signals
        view.create_recipe_category_requested.connect(self._on_create_recipe_cat)
        view.edit_recipe_category_requested.connect(self._on_edit_recipe_cat)
        view.delete_recipe_category_requested.connect(self._on_delete_recipe_cat)

        self._refresh()

    def set_shopping_list(self, shopping_list: ShoppingList) -> None:
        """Обновляет последний список покупок для экспорта из настроек."""
        self._last_shopping_list = shopping_list

    def refresh(self) -> None:
        self._refresh()

    def _refresh(self) -> None:
        try:
            members = self._list_uc.execute()
            self._view.set_family_members(members)
        except Exception as exc:
            self._view.show_error(str(exc))
        self._refresh_product_categories()
        self._refresh_recipe_categories()

    # ------------------------------------------------------------------
    # Family members
    # ------------------------------------------------------------------

    def _on_create(self, data: FamilyMemberData) -> None:
        try:
            self._create_uc.execute(data)
            self._refresh()
        except Exception as exc:
            self._view.show_error(str(exc))

    def _on_edit(self, member_id: object, data: FamilyMemberData) -> None:
        try:
            self._edit_uc.execute(FamilyMemberId(cast(int, member_id)), data)
            self._refresh()
        except Exception as exc:
            self._view.show_error(str(exc))

    def _on_delete(self, member_id: object) -> None:
        try:
            self._delete_uc.execute(FamilyMemberId(cast(int, member_id)))
            self._refresh()
        except Exception as exc:
            self._view.show_error(str(exc))

    # ------------------------------------------------------------------
    # Product categories
    # ------------------------------------------------------------------

    def _refresh_product_categories(self) -> None:
        try:
            categories = self._list_product_cat_uc.execute()
            self._view.set_product_categories(categories)
        except Exception as exc:
            self._view.show_error(str(exc))

    def _on_create_product_cat(self, name: str) -> None:
        try:
            self._create_product_cat_uc.execute(name)
            self._refresh_product_categories()
        except Exception as exc:
            self._view.show_error(str(exc))

    def _on_edit_product_cat(self, category_id: int, name: str) -> None:
        try:
            self._edit_product_cat_uc.execute(category_id, name)
            self._refresh_product_categories()
        except Exception as exc:
            self._view.show_error(str(exc))

    def _on_delete_product_cat(self, category_id: int) -> None:
        try:
            self._delete_product_cat_uc.execute(category_id)
            self._refresh_product_categories()
        except Exception as exc:
            self._view.show_error(str(exc))

    # ------------------------------------------------------------------
    # Recipe categories
    # ------------------------------------------------------------------

    def _refresh_recipe_categories(self) -> None:
        try:
            categories = self._list_recipe_cat_uc.execute()
            self._view.set_recipe_categories(categories)
        except Exception as exc:
            self._view.show_error(str(exc))

    def _on_create_recipe_cat(self, name: str) -> None:
        try:
            self._create_recipe_cat_uc.execute(name)
            self._refresh_recipe_categories()
        except Exception as exc:
            self._view.show_error(str(exc))

    def _on_edit_recipe_cat(self, category_id: int, name: str) -> None:
        try:
            self._edit_recipe_cat_uc.execute(category_id, name)
            self._refresh_recipe_categories()
        except Exception as exc:
            self._view.show_error(str(exc))

    def _on_delete_recipe_cat(self, category_id: int) -> None:
        try:
            self._delete_recipe_cat_uc.execute(category_id)
            self._refresh_recipe_categories()
        except Exception as exc:
            self._view.show_error(str(exc))

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def _on_export_text(self) -> None:
        if self._last_shopping_list is None:
            self._view.show_error("Сначала сформируйте список покупок.")
            return
        try:
            text = self._export_text_uc.execute(self._last_shopping_list)
            from PySide6.QtWidgets import (
                QDialog,
                QDialogButtonBox,
                QPlainTextEdit,
                QVBoxLayout,
            )

            dialog = QDialog(self._view)
            dialog.setWindowTitle("Список покупок (текст)")
            dialog.resize(500, 400)
            te = QPlainTextEdit(text)
            te.setReadOnly(True)
            buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
            buttons.rejected.connect(dialog.reject)
            layout = QVBoxLayout(dialog)
            layout.addWidget(te)
            layout.addWidget(buttons)
            dialog.exec()
        except Exception as exc:
            self._view.show_error(str(exc))

    def _on_export_csv(self, filepath: str) -> None:
        if self._last_shopping_list is None:
            self._view.show_error("Сначала сформируйте список покупок.")
            return
        try:
            self._export_csv_uc.execute(self._last_shopping_list, filepath)
        except Exception as exc:
            self._view.show_error(str(exc))
