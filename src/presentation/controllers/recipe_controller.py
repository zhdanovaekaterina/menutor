from typing import cast

from src.application.use_cases.manage_product import ListProducts
from src.application.use_cases.manage_recipe import (
    CreateRecipe,
    DeleteRecipe,
    EditRecipe,
    ListRecipes,
    RecipeData,
)
from src.domain.value_objects.types import RecipeId
from src.presentation.views.recipe_list_view import RecipeListView


class RecipeController:
    """Соединяет RecipeListView с use cases слоя Application."""

    def __init__(
        self,
        view: RecipeListView,
        create_uc: CreateRecipe,
        edit_uc: EditRecipe,
        delete_uc: DeleteRecipe,
        list_uc: ListRecipes,
        list_products_uc: ListProducts,
    ) -> None:
        self._view = view
        self._create_uc = create_uc
        self._edit_uc = edit_uc
        self._delete_uc = delete_uc
        self._list_uc = list_uc
        self._list_products_uc = list_products_uc

        view.create_recipe_requested.connect(self._on_create)
        view.edit_recipe_requested.connect(self._on_edit)
        view.delete_recipe_requested.connect(self._on_delete)

        self._refresh()

    def refresh(self) -> None:
        self._refresh()

    def _refresh(self) -> None:
        try:
            recipes = self._list_uc.execute()
            self._view.set_recipes(recipes)
            products = self._list_products_uc.execute()
            self._view.set_products(products)
        except Exception as exc:
            self._view.show_error(str(exc))

    def _on_create(self, data: RecipeData) -> None:
        try:
            self._create_uc.execute(data)
            self._refresh()
        except Exception as exc:
            self._view.show_error(str(exc))

    def _on_edit(self, recipe_id: object, data: RecipeData) -> None:
        try:
            self._edit_uc.execute(RecipeId(cast(int, recipe_id)), data)
            self._refresh()
        except Exception as exc:
            self._view.show_error(str(exc))

    def _on_delete(self, recipe_id: object) -> None:
        try:
            self._delete_uc.execute(RecipeId(cast(int, recipe_id)))
            self._refresh()
        except Exception as exc:
            self._view.show_error(str(exc))
