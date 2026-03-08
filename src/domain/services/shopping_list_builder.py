from src.domain.entities.family_member import FamilyMember
from src.domain.entities.menu import WeeklyMenu
from src.domain.entities.shopping_list import ShoppingList, ShoppingListItem
from src.domain.ports.product_category_repository import ProductCategoryRepository
from src.domain.ports.product_repository import ProductRepository
from src.domain.ports.recipe_repository import RecipeRepository
from src.domain.services.portion_calculator import PortionCalculator
from src.domain.services.unit_converter import UnitConverter
from src.domain.value_objects.quantity import Quantity
from src.domain.value_objects.types import ProductId


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
                scaled = recipe.scale_to(base)

                for ing in scaled.ingredients:
                    pid = ing.product_id
                    if pid in aggregated:
                        aggregated[pid] = aggregated[pid] + ing.quantity
                    else:
                        aggregated[pid] = ing.quantity
            elif slot.product_id is not None and slot.quantity is not None and slot.unit is not None:
                pid = slot.product_id
                qty = Quantity(slot.quantity, slot.unit)
                if pid in aggregated:
                    aggregated[pid] = aggregated[pid] + qty
                else:
                    aggregated[pid] = qty

        category_map = dict(self._product_category_repo.find_active())

        items: list[ShoppingListItem] = []
        for product_id, qty in aggregated.items():
            product = self._product_repo.get_by_id(product_id)
            if product is None:
                continue

            # Normalize to product's recipe_unit, then convert to purchase unit
            recipe_qty = qty.convert_to(product.recipe_unit)
            purchase_qty, cost = product.compute_purchase(recipe_qty.amount)

            items.append(ShoppingListItem(
                product_id=product_id,
                product_name=product.name,
                category=category_map.get(product.category_id, ""),
                quantity=purchase_qty,
                cost=cost,
            ))

        return ShoppingList(items=items)
