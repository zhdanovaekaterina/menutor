from backend.domain.entities.preference import Preference
from backend.domain.entities.recipe import Recipe
from backend.domain.ports.product_repository import ProductRepository
from backend.domain.ports.recipe_repository import RecipeRepository
from backend.domain.value_objects.preference_enums import PreferenceMode, PreferenceType
from backend.domain.value_objects.types import ProductCategoryId, ProductId, RecipeId


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
        all_category_ids, has_uncategorized = self._resolve_category_ids(all_product_ids)

        if preference.type == PreferenceType.ALLERGY:
            return self._matches_allergy(all_product_ids, all_category_ids, preference)

        if preference.mode == PreferenceMode.BLOCKED:
            return self._matches_blocked(all_category_ids, preference)

        # ALLOWED mode
        return self._matches_allowed(all_product_ids, all_category_ids, preference, has_uncategorized)

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
        category_ids: set[ProductCategoryId],
        preference: Preference,
    ) -> bool:
        blocked_products = set(preference.product_ids)
        blocked_categories = set(preference.category_ids)
        if product_ids & blocked_products:
            return False
        if category_ids & blocked_categories:
            return False
        return True

    @staticmethod
    def _matches_blocked(
        category_ids: set[ProductCategoryId],
        preference: Preference,
    ) -> bool:
        blocked = set(preference.category_ids)
        return not (category_ids & blocked)

    @staticmethod
    def _matches_allowed(
        product_ids: set[ProductId],
        category_ids: set[ProductCategoryId],
        preference: Preference,
        has_uncategorized: bool = False,
    ) -> bool:
        if not product_ids:
            return False  # EC-1: empty recipe does not satisfy ALLOWED
        if has_uncategorized:
            return False  # BR-9: products without a category not in any allowed set
        allowed = set(preference.category_ids)
        for cid in category_ids:
            if cid not in allowed:
                return False
        return True
