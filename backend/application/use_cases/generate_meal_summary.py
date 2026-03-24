"""Use case: generate a meal summary for a menu."""

from dataclasses import dataclass, field

from backend.domain.entities.menu import MenuSlot
from backend.domain.exceptions import EntityNotFoundError
from backend.domain.ports.menu_repository import MenuRepository
from backend.domain.ports.product_repository import ProductRepository
from backend.domain.ports.recipe_repository import RecipeRepository
from backend.domain.services.shopping_list_builder import (
    IngredientNode,
    ShoppingListBuilder,
)
from backend.domain.value_objects.types import MenuId, ProductId, RecipeId, UserId


@dataclass
class MealOccurrence:
    day: int
    meal_type: str
    servings: float
    pieces_override: int | None = None
    slot_index: int = 0


@dataclass
class MealSummaryRecipe:
    recipe_id: RecipeId
    recipe_name: str
    occurrences: list[MealOccurrence]
    total_servings: float
    pieces_info: dict | None  # {"total_pieces": int, "pieces_per_portion": int} or None
    ingredients: list[IngredientNode]


@dataclass
class MealSummaryProduct:
    product_id: ProductId
    product_name: str
    occurrences: list[dict]  # [{"day": int, "meal_type": str, "quantity": float, "unit": str, "slot_index": int}]
    total_quantity: float
    unit: str


@dataclass
class MealSummaryResponse:
    menu_id: MenuId
    menu_name: str
    recipes: list[MealSummaryRecipe]
    products: list[MealSummaryProduct]


class GenerateMealSummary:
    def __init__(
        self,
        menu_repo: MenuRepository,
        recipe_repo: RecipeRepository,
        product_repo: ProductRepository,
        builder: ShoppingListBuilder,
    ) -> None:
        self._menu_repo = menu_repo
        self._recipe_repo = recipe_repo
        self._product_repo = product_repo
        self._builder = builder

    def execute(self, menu_id: MenuId, user_id: UserId) -> MealSummaryResponse:
        menu = self._menu_repo.get_by_id(menu_id)
        if menu is None or menu.user_id != user_id:
            raise EntityNotFoundError(f"Меню {menu_id} не найдено")

        # Group slots by recipe_id and product_id
        recipe_slots: dict[RecipeId, list[tuple[int, MenuSlot]]] = {}
        product_slots: dict[ProductId, list[tuple[int, MenuSlot]]] = {}

        for idx, slot in enumerate(menu.slots):
            if slot.recipe_id is not None:
                recipe_slots.setdefault(slot.recipe_id, []).append((idx, slot))
            elif slot.product_id is not None:
                product_slots.setdefault(slot.product_id, []).append((idx, slot))

        # Build recipe summaries
        recipe_summaries: list[MealSummaryRecipe] = []
        for recipe_id, indexed_slots in recipe_slots.items():
            recipe = self._recipe_repo.get_by_id(recipe_id)
            if recipe is None:
                continue

            occurrences: list[MealOccurrence] = []
            total_servings: float = 0.0

            for idx, slot in indexed_slots:
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
                    # Convert pieces back to servings for display
                    servings_for_slot = pcs / recipe.pieces_per_portion
                else:
                    servings_for_slot = float(
                        slot.servings_override
                        if slot.servings_override is not None
                        else recipe.servings
                    )

                total_servings += servings_for_slot
                occurrences.append(MealOccurrence(
                    day=slot.day,
                    meal_type=slot.meal_type,
                    servings=servings_for_slot,
                    pieces_override=slot.pieces_override,
                    slot_index=idx,
                ))

            # Calculate scale factor for total servings
            if recipe.is_pieces_mode:
                assert recipe.total_pieces is not None
                assert recipe.pieces_per_portion is not None
                total_pcs = round(total_servings * recipe.pieces_per_portion)
                scale_factor = total_pcs / recipe.total_pieces
            else:
                scale_factor = total_servings / recipe.servings

            ingredients = self._builder.resolve_recipe_ingredients_tree(
                recipe, scale_factor
            )

            pieces_info = None
            if recipe.is_pieces_mode:
                assert recipe.total_pieces is not None
                assert recipe.pieces_per_portion is not None
                pieces_info = {
                    "total_pieces": round(total_servings * recipe.pieces_per_portion),
                    "pieces_per_portion": recipe.pieces_per_portion,
                }

            recipe_summaries.append(MealSummaryRecipe(
                recipe_id=recipe_id,
                recipe_name=recipe.name,
                occurrences=occurrences,
                total_servings=total_servings,
                pieces_info=pieces_info,
                ingredients=ingredients,
            ))

        # Build product summaries
        product_summaries: list[MealSummaryProduct] = []
        for product_id, indexed_slots in product_slots.items():
            product = self._product_repo.get_by_id(product_id)
            if product is None:
                continue

            occurrences_list: list[dict] = []
            total_quantity: float = 0.0
            unit: str = ""

            for idx, slot in indexed_slots:
                qty = slot.quantity or 0.0
                u = slot.unit or ""
                total_quantity += qty
                unit = u  # last wins (all should be same unit)
                occurrences_list.append({
                    "day": slot.day,
                    "meal_type": slot.meal_type,
                    "quantity": qty,
                    "unit": u,
                    "slot_index": idx,
                })

            product_summaries.append(MealSummaryProduct(
                product_id=product_id,
                product_name=product.name,
                occurrences=occurrences_list,
                total_quantity=total_quantity,
                unit=unit,
            ))

        return MealSummaryResponse(
            menu_id=menu.id,
            menu_name=menu.name,
            recipes=recipe_summaries,
            products=product_summaries,
        )
