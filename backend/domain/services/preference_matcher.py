from backend.domain.entities.preference import Preference
from backend.domain.entities.recipe import Recipe
from backend.domain.ports.product_repository import ProductRepository
from backend.domain.ports.recipe_repository import RecipeRepository
from backend.domain.value_objects.preference_enums import PreferenceMode, PreferenceType
from backend.domain.value_objects.types import (
    ProductCategoryId,
    ProductId,
    RecipeCategoryId,
    RecipeId,
)


class PreferenceMatcher:
    """Computes which preferences a recipe satisfies.

    Pure computation over resolved ingredient data.
    Needs repository access to recursively resolve sub-recipe ingredients
    and to look up product categories.
    """

    def __init__(
        self,
        recipe_repo: RecipeRepository,
        product_repo: ProductRepository,
    ) -> None:
        self._recipe_repo = recipe_repo
        self._product_repo = product_repo

    def matches_preference(self, recipe: Recipe, preference: Preference) -> bool:
        """Return True if the recipe satisfies (is compatible with) the given preference."""
        all_product_ids = self._resolve_all_product_ids(recipe, set())
        all_product_category_ids, has_uncategorized_product = self._resolve_category_ids(all_product_ids)
        all_recipe_category_ids, has_uncategorized_recipe = self._resolve_all_recipe_category_ids(recipe, set())

        if preference.type == PreferenceType.ALLERGY:
            return self._matches_allergy(
                all_product_ids, all_product_category_ids, all_recipe_category_ids, preference
            )

        if preference.mode == PreferenceMode.BLOCKED:
            return self._matches_blocked(all_product_category_ids, all_recipe_category_ids, preference)

        # ALLOWED mode
        return self._matches_allowed(
            all_product_ids, all_product_category_ids, all_recipe_category_ids,
            preference, has_uncategorized_product, has_uncategorized_recipe,
        )

    def match_all(self, recipe: Recipe, preferences: list[Preference]) -> list[Preference]:
        """Return the subset of preferences that the recipe satisfies."""
        return [p for p in preferences if self.matches_preference(recipe, p)]

    def _resolve_all_product_ids(
        self, recipe: Recipe, visited: set[RecipeId]
    ) -> set[ProductId]:
        """Recursively collect all product IDs from a recipe and its sub-recipes."""
        if recipe.id in visited:
            return set()
        visited.add(recipe.id)
        product_ids: set[ProductId] = set()
        for ing in recipe.ingredients:
            if ing.is_product:
                assert ing.product_id is not None
                product_ids.add(ing.product_id)
            elif ing.is_sub_recipe:
                assert ing.sub_recipe_id is not None
                sub = self._recipe_repo.get_by_id(ing.sub_recipe_id)
                if sub is not None:
                    product_ids |= self._resolve_all_product_ids(sub, visited)
        visited.discard(recipe.id)
        return product_ids

    def _resolve_all_recipe_category_ids(
        self, recipe: Recipe, visited: set[RecipeId]
    ) -> tuple[set[RecipeCategoryId], bool]:
        """Recursively collect recipe category IDs from a recipe and its sub-recipes.

        Returns (category_ids, has_uncategorized) where has_uncategorized is True
        if any recipe in the tree has category_id == 0.
        """
        if recipe.id in visited:
            return set(), False
        visited.add(recipe.id)
        category_ids: set[RecipeCategoryId] = set()
        has_uncategorized = False
        if recipe.category_id == RecipeCategoryId(0):
            has_uncategorized = True
        else:
            category_ids.add(recipe.category_id)
        for ing in recipe.ingredients:
            if ing.is_sub_recipe:
                assert ing.sub_recipe_id is not None
                sub = self._recipe_repo.get_by_id(ing.sub_recipe_id)
                if sub is not None:
                    sub_cats, sub_uncategorized = self._resolve_all_recipe_category_ids(sub, visited)
                    category_ids |= sub_cats
                    has_uncategorized = has_uncategorized or sub_uncategorized
        visited.discard(recipe.id)
        return category_ids, has_uncategorized

    def _resolve_category_ids(
        self, product_ids: set[ProductId]
    ) -> tuple[set[ProductCategoryId], bool]:
        """Look up category IDs for a set of product IDs.

        Returns (category_ids, has_uncategorized) where has_uncategorized is True
        if any product exists with category_id == 0 (BR-9).
        """
        category_ids: set[ProductCategoryId] = set()
        has_uncategorized = False
        for pid in product_ids:
            product = self._product_repo.get_by_id(pid)
            if product is not None:
                if product.category_id == ProductCategoryId(0):
                    has_uncategorized = True
                else:
                    category_ids.add(product.category_id)
        return category_ids, has_uncategorized

    @staticmethod
    def _matches_allergy(
        product_ids: set[ProductId],
        product_category_ids: set[ProductCategoryId],
        recipe_category_ids: set[RecipeCategoryId],
        preference: Preference,
    ) -> bool:
        if product_ids & set(preference.product_ids):
            return False
        if product_category_ids & set(preference.category_ids):
            return False
        if recipe_category_ids & set(preference.recipe_category_ids):
            return False
        return True

    @staticmethod
    def _matches_blocked(
        product_category_ids: set[ProductCategoryId],
        recipe_category_ids: set[RecipeCategoryId],
        preference: Preference,
    ) -> bool:
        if product_category_ids & set(preference.category_ids):
            return False
        if recipe_category_ids & set(preference.recipe_category_ids):
            return False
        return True

    @staticmethod
    def _matches_allowed(
        product_ids: set[ProductId],
        product_category_ids: set[ProductCategoryId],
        recipe_category_ids: set[RecipeCategoryId],
        preference: Preference,
        has_uncategorized_product: bool = False,
        has_uncategorized_recipe: bool = False,
    ) -> bool:
        product_check_needed = bool(preference.category_ids)
        recipe_check_needed = bool(preference.recipe_category_ids)

        if not product_check_needed and not recipe_check_needed:
            return False  # EC-1: empty ALLOWED preference matches nothing

        if product_check_needed:
            if not product_ids:
                return False  # no products to satisfy product category check
            if has_uncategorized_product:
                return False  # BR-9: uncategorized product not in any allowed set
            allowed_products = set(preference.category_ids)
            for cid in product_category_ids:
                if cid not in allowed_products:
                    return False

        if recipe_check_needed:
            if has_uncategorized_recipe:
                return False  # recipe without category not in any allowed set
            allowed_recipes = set(preference.recipe_category_ids)
            for cid in recipe_category_ids:
                if cid not in allowed_recipes:
                    return False

        return True
