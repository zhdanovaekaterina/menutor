from backend.domain.entities.menu import WeeklyMenu
from backend.domain.entities.recipe import Recipe
from backend.domain.entities.shopping_list import ShoppingList, ShoppingListItem
from backend.domain.exceptions import SubRecipeWeightError, UnitConversionError
from backend.domain.ports.product_category_repository import ProductCategoryRepository
from backend.domain.ports.product_repository import ProductRepository
from backend.domain.ports.recipe_repository import RecipeRepository
from backend.domain.services.portion_calculator import PortionCalculator
from backend.domain.services.unit_converter import UnitConverter
from backend.domain.value_objects.quantity import Quantity
from backend.domain.value_objects.types import ProductId, RecipeId


class ShoppingListBuilder:
    def __init__(
        self,
        recipe_repo: RecipeRepository,
        product_repo: ProductRepository,
        product_category_repo: ProductCategoryRepository,
        portion_calc: PortionCalculator,
        unit_converter: UnitConverter,
    ) -> None:
        self._recipe_repo = recipe_repo
        self._product_repo = product_repo
        self._product_category_repo = product_category_repo
        self._portion_calc = portion_calc
        self._unit_converter = unit_converter

    def build(self, menu: WeeklyMenu) -> ShoppingList:
        aggregated: dict[ProductId, Quantity] = {}

        for slot in menu.slots:
            if slot.recipe_id is not None:
                recipe = self._recipe_repo.get_by_id(slot.recipe_id)
                if recipe is None:
                    continue

                base = float(slot.servings_override if slot.servings_override is not None
                             else recipe.servings)
                scale_factor = base / recipe.servings

                slot_products = self._resolve_recipe_products(recipe, scale_factor, set())
                for pid, qty in slot_products.items():
                    if pid in aggregated:
                        try:
                            aggregated[pid] = aggregated[pid] + qty
                        except UnitConversionError:
                            pass  # keep existing, skip incompatible ingredient
                    else:
                        aggregated[pid] = qty

            elif slot.product_id is not None and slot.quantity is not None and slot.unit is not None:
                pid = slot.product_id
                try:
                    qty = Quantity(slot.quantity, slot.unit)
                except UnitConversionError:
                    continue
                if pid in aggregated:
                    try:
                        aggregated[pid] = aggregated[pid] + qty
                    except UnitConversionError:
                        pass  # keep existing, skip incompatible quantity
                else:
                    aggregated[pid] = qty

        category_map = dict(self._product_category_repo.find_active())

        items: list[ShoppingListItem] = []
        for product_id, qty in aggregated.items():
            product = self._product_repo.get_by_id(product_id)
            if product is None:
                continue

            # Normalize to product's recipe_unit, then convert to purchase unit
            try:
                recipe_qty = qty.convert_to(product.recipe_unit)
            except UnitConversionError:
                continue  # skip product with incompatible units
            purchase_qty, cost = product.compute_purchase(recipe_qty.amount)

            items.append(ShoppingListItem(
                product_id=product_id,
                product_name=product.name,
                category=category_map.get(product.category_id, ""),
                quantity=purchase_qty,
                cost=cost,
                recipe_quantity=recipe_qty,
            ))

        return ShoppingList(items=items)

    def _resolve_recipe_products(
        self,
        recipe: Recipe,
        scale_factor: float,
        visited: set[RecipeId],
    ) -> dict[ProductId, Quantity]:
        if recipe.id in visited:
            return {}  # defensive guard against cycles
        visited.add(recipe.id)
        products: dict[ProductId, Quantity] = {}
        for ing in recipe.ingredients:
            scaled_amount = ing.quantity.amount * scale_factor
            if ing.is_product:
                assert ing.product_id is not None
                qty = Quantity(scaled_amount, ing.quantity.unit)
                if ing.product_id in products:
                    try:
                        products[ing.product_id] = products[ing.product_id] + qty
                    except UnitConversionError:
                        pass
                else:
                    products[ing.product_id] = qty
            elif ing.is_sub_recipe:
                assert ing.sub_recipe_id is not None
                sub_recipe = self._recipe_repo.get_by_id(ing.sub_recipe_id)
                if sub_recipe is None:
                    continue
                if ing.quantity.is_weight:
                    qty_in_g = ing.quantity.convert_to("g").amount * scale_factor
                    if sub_recipe.weight == 0:
                        raise SubRecipeWeightError(
                            f"Рецепт «{sub_recipe.name}» имеет нулевой вес. "
                            "Укажите вес рецепта или используйте порции."
                        )
                    sub_scale = qty_in_g / sub_recipe.weight
                else:
                    sub_scale = scaled_amount / sub_recipe.servings
                sub_products = self._resolve_recipe_products(sub_recipe, sub_scale, visited)
                for pid, qty in sub_products.items():
                    if pid in products:
                        try:
                            products[pid] = products[pid] + qty
                        except UnitConversionError:
                            pass
                    else:
                        products[pid] = qty
        visited.discard(recipe.id)
        return products

    def flatten_recipe_products(self, recipe: Recipe) -> dict[ProductId, Quantity]:
        return self._resolve_recipe_products(recipe, 1.0, set())
