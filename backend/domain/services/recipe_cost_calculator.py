from dataclasses import dataclass
from decimal import Decimal

from backend.domain.entities.product import Product
from backend.domain.entities.recipe import Recipe
from backend.domain.value_objects.money import Money
from backend.domain.value_objects.quantity import Quantity
from backend.domain.value_objects.types import ProductId


@dataclass(frozen=True)
class IngredientCost:
    """Cost of a single ingredient in the flat product map."""
    product_id: ProductId
    product_name: str
    quantity: Quantity
    cost: Money | None          # None if unit conversion failed
    has_price: bool             # False if price_per_purchase_unit.amount == 0


@dataclass(frozen=True)
class RecipeCostResult:
    """Result of cost calculation for a recipe."""
    cost_per_portion: Decimal | None  # None if cannot be calculated
    total_cost: Decimal | None        # total recipe cost (all servings)
    currency: str | None              # e.g. "RUB"
    is_partial: bool                  # True if any ingredient lacks a price
    computed_servings: int
    ingredient_costs: list[IngredientCost]  # breakdown per product


class RecipeCostCalculator:
    """Calculates recipe cost per portion from a flat product map.

    Pure domain service -- receives data, no repository access.
    """

    def calculate(
        self,
        recipe: Recipe,
        flat_products: dict[ProductId, Quantity],
        product_lookup: dict[ProductId, Product],
    ) -> RecipeCostResult:
        """Calculate cost per portion for a recipe.

        Args:
            recipe: The recipe entity (for computed_servings).
            flat_products: Output of ShoppingListBuilder.flatten_recipe_products().
            product_lookup: ProductId -> Product mapping for all products in flat_products.
        """
        if not flat_products:
            return RecipeCostResult(
                cost_per_portion=None,
                total_cost=None,
                currency=None,
                is_partial=False,
                computed_servings=recipe.computed_servings,
                ingredient_costs=[],
            )

        ingredient_costs: list[IngredientCost] = []
        total = Decimal("0")
        currency: str | None = None
        is_partial = False
        currency_mismatch = False

        for pid, qty in flat_products.items():
            product = product_lookup.get(pid)
            if product is None:
                is_partial = True
                ingredient_costs.append(IngredientCost(
                    product_id=pid,
                    product_name=f"[deleted #{int(pid)}]",
                    quantity=qty,
                    cost=None,
                    has_price=False,
                ))
                continue

            has_price = product.price_per_purchase_unit.amount > 0
            if not has_price:
                is_partial = True

            try:
                recipe_qty = qty.convert_to(product.recipe_unit)
            except Exception:
                is_partial = True
                ingredient_costs.append(IngredientCost(
                    product_id=pid,
                    product_name=product.name,
                    quantity=qty,
                    cost=None,
                    has_price=has_price,
                ))
                continue

            _, cost = product.compute_purchase(recipe_qty.amount)

            if currency is None:
                currency = cost.currency
            elif currency != cost.currency:
                currency_mismatch = True

            total += cost.amount
            ingredient_costs.append(IngredientCost(
                product_id=pid,
                product_name=product.name,
                quantity=qty,
                cost=cost,
                has_price=has_price,
            ))

        if currency_mismatch:
            return RecipeCostResult(
                cost_per_portion=None,
                total_cost=None,
                currency=None,
                is_partial=True,
                computed_servings=recipe.computed_servings,
                ingredient_costs=ingredient_costs,
            )

        servings = recipe.computed_servings
        cost_per_portion = round(total / servings, 2) if servings > 0 else None

        return RecipeCostResult(
            cost_per_portion=cost_per_portion,
            total_cost=round(total, 2),
            currency=currency,
            is_partial=is_partial,
            computed_servings=servings,
            ingredient_costs=ingredient_costs,
        )
