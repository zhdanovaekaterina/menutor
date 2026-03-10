import logging
from typing import Callable, cast

from PySide6.QtWidgets import QMessageBox

from backend.application.use_cases.manage_category import (
    ActivateCategory,
    CheckCategoryUsed,
    CreateCategory,
    DeleteCategory,
    EditCategory,
    HardDeleteCategory,
    ListAllCategories,
)
from backend.application.use_cases.manage_family import (
    CreateFamilyMember,
    DeleteFamilyMember,
    EditFamilyMember,
    FamilyMemberData,
    ListFamilyMembers,
)
from backend.domain.exceptions import AppError
from backend.domain.value_objects.category import Category
from backend.domain.value_objects.types import FamilyMemberId
from backend.presentation.views.settings_view import SettingsView
from backend.presentation.widgets.category_panel import CategoryPanel

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
        hard_delete_uc: HardDeleteCategory,
        activate_uc: ActivateCategory,
        check_uc: CheckCategoryUsed,
        set_categories: Callable[[list[Category]], None],
        show_error: Callable[[str], None],
    ) -> None:
        self._panel = panel
        self._list_uc = list_uc
        self._create_uc = create_uc
        self._edit_uc = edit_uc
        self._delete_uc = delete_uc
        self._hard_delete_uc = hard_delete_uc
        self._activate_uc = activate_uc
        self._check_uc = check_uc
        self._set_categories = set_categories
        self._show_error = show_error

        panel.create_requested.connect(self._on_create)
        panel.edit_requested.connect(self._on_edit)
        panel.delete_requested.connect(self._on_delete)
        panel.activate_requested.connect(self._on_activate)

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
            if not self._check_uc.execute(category_id):
                self._hard_delete_uc.execute(category_id)
                self.refresh()
                return

            msg = QMessageBox(self._panel)
            msg.setWindowTitle("Удаление категории")
            msg.setText(
                "К этой категории привязаны элементы.\n"
                "Что вы хотите сделать?"
            )
            delete_btn = msg.addButton(
                "Удалить с элементами", QMessageBox.ButtonRole.DestructiveRole
            )
            hide_btn = msg.addButton(
                "Скрыть категорию", QMessageBox.ButtonRole.AcceptRole
            )
            msg.addButton("Отмена", QMessageBox.ButtonRole.RejectRole)
            msg.exec()

            clicked = msg.clickedButton()
            if clicked is delete_btn:
                self._hard_delete_uc.execute(category_id)
                self.refresh()
            elif clicked is hide_btn:
                self._delete_uc.execute(category_id)
                self.refresh()
        except AppError as exc:
            logger.warning("Ошибка при удалении категории %s: %s", category_id, exc)
            self._show_error(str(exc))

    def _on_activate(self, category_id: int) -> None:
        try:
            self._activate_uc.execute(category_id)
            self.refresh()
        except AppError as exc:
            logger.warning("Ошибка при активации категории %s: %s", category_id, exc)
            self._show_error(str(exc))


class SettingsController:
    """Соединяет SettingsView с use cases семьи и категорий."""

    def __init__(
        self,
        view: SettingsView,
        create_member_uc: CreateFamilyMember,
        edit_member_uc: EditFamilyMember,
        delete_member_uc: DeleteFamilyMember,
        list_members_uc: ListFamilyMembers,
        # Product categories
        list_product_categories_uc: ListAllCategories,
        create_product_category_uc: CreateCategory,
        edit_product_category_uc: EditCategory,
        delete_product_category_uc: DeleteCategory,
        hard_delete_product_category_uc: HardDeleteCategory,
        activate_product_category_uc: ActivateCategory,
        check_product_category_used_uc: CheckCategoryUsed,
        # Recipe categories
        list_recipe_categories_uc: ListAllCategories,
        create_recipe_category_uc: CreateCategory,
        edit_recipe_category_uc: EditCategory,
        delete_recipe_category_uc: DeleteCategory,
        hard_delete_recipe_category_uc: HardDeleteCategory,
        activate_recipe_category_uc: ActivateCategory,
        check_recipe_category_used_uc: CheckCategoryUsed,
    ) -> None:
        self._view = view
        self._create_uc = create_member_uc
        self._edit_uc = edit_member_uc
        self._delete_uc = delete_member_uc
        self._list_uc = list_members_uc

        # Category handlers (replaces duplicate product/recipe category methods)
        self._product_cat_handler = _CategoryHandler(
            panel=view.product_cat_panel,
            list_uc=list_product_categories_uc,
            create_uc=create_product_category_uc,
            edit_uc=edit_product_category_uc,
            delete_uc=delete_product_category_uc,
            hard_delete_uc=hard_delete_product_category_uc,
            activate_uc=activate_product_category_uc,
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
            hard_delete_uc=hard_delete_recipe_category_uc,
            activate_uc=activate_recipe_category_uc,
            check_uc=check_recipe_category_used_uc,
            set_categories=view.set_recipe_categories,
            show_error=view.show_error,
        )

        # Family member signals
        view.create_member_requested.connect(self._on_create)
        view.edit_member_requested.connect(self._on_edit)
        view.delete_member_requested.connect(self._on_delete)

        self._refresh()

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

