import logging
from typing import Callable, cast

from src.application.use_cases.import_export import (
    ExportShoppingListAsCsv,
    ExportShoppingListAsText,
)
from src.application.use_cases.manage_category import (
    CheckCategoryUsed,
    CreateCategory,
    DeleteCategory,
    EditCategory,
    ListAllCategories,
)
from src.application.use_cases.manage_family import (
    CreateFamilyMember,
    DeleteFamilyMember,
    EditFamilyMember,
    FamilyMemberData,
    ListFamilyMembers,
)
from src.domain.entities.shopping_list import ShoppingList
from src.domain.exceptions import AppError
from src.domain.value_objects.category import Category
from src.domain.value_objects.types import FamilyMemberId
from src.presentation.views.settings_view import SettingsView
from src.presentation.widgets.category_panel import CategoryPanel

logger = logging.getLogger(__name__)


class _CategoryHandler:
    """Handles CRUD signals for one CategoryPanel."""

    def __init__(
        self,
        panel: CategoryPanel,
        list_uc: ListAllCategories,
        create_uc: CreateCategory,
        edit_uc: EditCategory,
        delete_uc: DeleteCategory,
        check_uc: CheckCategoryUsed,
        set_categories: Callable[[list[Category]], None],
        show_error: Callable[[str], None],
    ) -> None:
        self._list_uc = list_uc
        self._create_uc = create_uc
        self._edit_uc = edit_uc
        self._delete_uc = delete_uc
        self._check_uc = check_uc
        self._set_categories = set_categories
        self._show_error = show_error

        panel.create_requested.connect(self._on_create)
        panel.edit_requested.connect(self._on_edit)
        panel.delete_requested.connect(self._on_delete)

    def refresh(self) -> None:
        try:
            categories = self._list_uc.execute()
            self._set_categories(categories)
        except AppError as exc:
            logger.warning("Ошибка при загрузке категорий: %s", exc)
            self._show_error(str(exc))

    def _on_create(self, name: str) -> None:
        try:
            self._create_uc.execute(name)
            self.refresh()
        except AppError as exc:
            logger.warning("Ошибка при создании категории: %s", exc)
            self._show_error(str(exc))

    def _on_edit(self, category_id: int, name: str) -> None:
        try:
            self._edit_uc.execute(category_id, name)
            self.refresh()
        except AppError as exc:
            logger.warning("Ошибка при редактировании категории %s: %s", category_id, exc)
            self._show_error(str(exc))

    def _on_delete(self, category_id: int) -> None:
        try:
            self._delete_uc.execute(category_id)
            self.refresh()
        except AppError as exc:
            logger.warning("Ошибка при удалении категории %s: %s", category_id, exc)
            self._show_error(str(exc))


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
        list_product_categories_uc: ListAllCategories,
        create_product_category_uc: CreateCategory,
        edit_product_category_uc: EditCategory,
        delete_product_category_uc: DeleteCategory,
        check_product_category_used_uc: CheckCategoryUsed,
        # Recipe categories
        list_recipe_categories_uc: ListAllCategories,
        create_recipe_category_uc: CreateCategory,
        edit_recipe_category_uc: EditCategory,
        delete_recipe_category_uc: DeleteCategory,
        check_recipe_category_used_uc: CheckCategoryUsed,
    ) -> None:
        self._view = view
        self._create_uc = create_member_uc
        self._edit_uc = edit_member_uc
        self._delete_uc = delete_member_uc
        self._list_uc = list_members_uc
        self._export_text_uc = export_text_uc
        self._export_csv_uc = export_csv_uc
        self._last_shopping_list: ShoppingList | None = None

        # Category handlers (replaces duplicate product/recipe category methods)
        self._product_cat_handler = _CategoryHandler(
            panel=view.product_cat_panel,
            list_uc=list_product_categories_uc,
            create_uc=create_product_category_uc,
            edit_uc=edit_product_category_uc,
            delete_uc=delete_product_category_uc,
            check_uc=check_product_category_used_uc,
            set_categories=view.set_product_categories,
            show_error=view.show_error,
        )
        self._recipe_cat_handler = _CategoryHandler(
            panel=view.recipe_cat_panel,
            list_uc=list_recipe_categories_uc,
            create_uc=create_recipe_category_uc,
            edit_uc=edit_recipe_category_uc,
            delete_uc=delete_recipe_category_uc,
            check_uc=check_recipe_category_used_uc,
            set_categories=view.set_recipe_categories,
            show_error=view.show_error,
        )

        # Family member signals
        view.create_member_requested.connect(self._on_create)
        view.edit_member_requested.connect(self._on_edit)
        view.delete_member_requested.connect(self._on_delete)

        # Export signals
        view.export_text_requested.connect(self._on_export_text)
        view.export_csv_requested.connect(self._on_export_csv)

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
        except AppError as exc:
            logger.warning("Ошибка при загрузке членов семьи: %s", exc)
            self._view.show_error(str(exc))
        self._product_cat_handler.refresh()
        self._recipe_cat_handler.refresh()

    # ------------------------------------------------------------------
    # Family members
    # ------------------------------------------------------------------

    def _on_create(self, data: FamilyMemberData) -> None:
        try:
            self._create_uc.execute(data)
            self._refresh()
        except AppError as exc:
            logger.warning("Ошибка при создании члена семьи: %s", exc)
            self._view.show_error(str(exc))

    def _on_edit(self, member_id: object, data: FamilyMemberData) -> None:
        try:
            self._edit_uc.execute(FamilyMemberId(cast(int, member_id)), data)
            self._refresh()
        except AppError as exc:
            logger.warning("Ошибка при редактировании члена семьи %s: %s", member_id, exc)
            self._view.show_error(str(exc))

    def _on_delete(self, member_id: object) -> None:
        try:
            self._delete_uc.execute(FamilyMemberId(cast(int, member_id)))
            self._refresh()
        except AppError as exc:
            logger.warning("Ошибка при удалении члена семьи %s: %s", member_id, exc)
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
        except AppError as exc:
            logger.warning("Ошибка при экспорте текста: %s", exc)
            self._view.show_error(str(exc))

    def _on_export_csv(self, filepath: str) -> None:
        if self._last_shopping_list is None:
            self._view.show_error("Сначала сформируйте список покупок.")
            return
        try:
            self._export_csv_uc.execute(self._last_shopping_list, filepath)
        except AppError as exc:
            logger.warning("Ошибка при экспорте CSV в %s: %s", filepath, exc)
            self._view.show_error(str(exc))
