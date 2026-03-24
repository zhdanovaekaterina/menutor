import math
from dataclasses import dataclass, field

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


@dataclass
class IngredientNode:
    """A node in the ingredient tree for meal summary display."""
    product_id: ProductId | None
    product_name: str
    quantity_amount: float
    quantity_unit: str
    sub_recipe_id: RecipeId | None = None
    sub_recipe_name: str | None = None
    children: list["IngredientNode"] = field(default_factory=list)


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

                if recipe.is_pieces_mode:
                    assert recipe.total_pieces is not None
                    assert recipe.pieces_per_portion is not None
                    if slot.pieces_override is not None:
                        pcs = slot.pieces_override
                    else:
                        portions = float(
                            slot.servings_override
                            if slot.servings_override is not None
                            else recipe.servings
                        )
                        pcs = max(1, round(portions * recipe.pieces_per_portion))
                    scale_factor = pcs / recipe.total_pieces
                else:
                    base = float(
                        slot.servings_override
                        if slot.servings_override is not None
                        else recipe.servings
                    )
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
            # Round up pcs quantities to integer before purchase calculation
            recipe_amount = recipe_qty.amount
            if recipe_qty.unit == "pcs":
                recipe_amount = math.ceil(recipe_amount)
                recipe_qty = Quantity(recipe_amount, recipe_qty.unit)
            purchase_qty, _ = product.compute_purchase(recipe_amount)
            if purchase_qty.unit == "kg":
                buy_amount = round(purchase_qty.amount, 2)
            else:
                buy_amount = math.ceil(purchase_qty.amount)
            cost = product.purchase_cost(buy_amount)

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
                    if sub_recipe.is_pieces_mode:
                        assert sub_recipe.total_pieces is not None
                        assert sub_recipe.pieces_per_portion is not None
                        pcs = max(1, round(scaled_amount * sub_recipe.pieces_per_portion))
                        sub_scale = pcs / sub_recipe.total_pieces
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

    def build_filtered(self, menu: WeeklyMenu, slot_indices: set[int]) -> ShoppingList:
        """Build a shopping list using only the slots at the given indices."""
        filtered_slots = [
            slot for i, slot in enumerate(menu.slots) if i in slot_indices
        ]
        filtered_menu = WeeklyMenu(
            id=menu.id,
            name=menu.name,
            slots=filtered_slots,
            user_id=menu.user_id,
        )
        return self.build(filtered_menu)

    def resolve_recipe_ingredients_tree(
        self,
        recipe: Recipe,
        scale_factor: float,
        visited: set[RecipeId] | None = None,
    ) -> list[IngredientNode]:
        """Resolve ingredients into a hierarchical tree, preserving sub-recipe nesting."""
        if visited is None:
            visited = set()
        if recipe.id in visited:
            return []  # cycle guard
        visited.add(recipe.id)

        nodes: list[IngredientNode] = []
        for ing in recipe.ingredients:
            scaled_amount = ing.quantity.amount * scale_factor
            if ing.is_product:
                assert ing.product_id is not None
                product = self._product_repo.get_by_id(ing.product_id)
                product_name = product.name if product else f"Продукт не найден (ID: {int(ing.product_id)})"
                nodes.append(IngredientNode(
                    product_id=ing.product_id,
                    product_name=product_name,
                    quantity_amount=scaled_amount,
                    quantity_unit=ing.quantity.unit,
                ))
            elif ing.is_sub_recipe:
                assert ing.sub_recipe_id is not None
                sub_recipe = self._recipe_repo.get_by_id(ing.sub_recipe_id)
                if sub_recipe is None:
                    nodes.append(IngredientNode(
                        product_id=None,
                        product_name=f"Рецепт не найден (ID: {int(ing.sub_recipe_id)})",
                        quantity_amount=scaled_amount,
                        quantity_unit=ing.quantity.unit,
                        sub_recipe_id=ing.sub_recipe_id,
                    ))
                    continue

                # Compute sub-recipe scale
                if ing.quantity.is_weight:
                    qty_in_g = ing.quantity.convert_to("g").amount * scale_factor
                    if sub_recipe.weight == 0:
                        # Zero-weight warning case: include node but no children
                        nodes.append(IngredientNode(
                            product_id=None,
                            product_name="",
                            quantity_amount=scaled_amount,
                            quantity_unit=ing.quantity.unit,
                            sub_recipe_id=ing.sub_recipe_id,
                            sub_recipe_name=sub_recipe.name,
                            children=[],  # empty -- frontend shows warning
                        ))
                        continue
                    sub_scale = qty_in_g / sub_recipe.weight
                else:
                    if sub_recipe.is_pieces_mode:
                        assert sub_recipe.total_pieces is not None
                        assert sub_recipe.pieces_per_portion is not None
                        pcs = max(1, round(scaled_amount * sub_recipe.pieces_per_portion))
                        sub_scale = pcs / sub_recipe.total_pieces
                    else:
                        sub_scale = scaled_amount / sub_recipe.servings

                children = self.resolve_recipe_ingredients_tree(sub_recipe, sub_scale, visited)
                nodes.append(IngredientNode(
                    product_id=None,
                    product_name="",
                    quantity_amount=scaled_amount,
                    quantity_unit=ing.quantity.unit,
                    sub_recipe_id=ing.sub_recipe_id,
                    sub_recipe_name=sub_recipe.name,
                    children=children,
                ))

        visited.discard(recipe.id)
        return nodes
