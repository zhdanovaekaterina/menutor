"""Конвертеры между доменными объектами и Pydantic-схемами."""

from collections.abc import Callable

from backend.api.schemas.category import ActiveCategoryResponse, CategoryResponse
from backend.api.schemas.family import FamilyMemberCreate, FamilyMemberResponse
from backend.api.schemas.meal_summary import (
    MealIngredientSchema,
    MealOccurrenceSchema,
    MealSummaryProductOccurrence,
    MealSummaryProductSchema,
    MealSummaryRecipeSchema,
    MealSummaryResponseSchema,
    PiecesInfoSchema,
)
from backend.api.schemas.meal_type import (
    MealTypeResponse,
    MealTypeUsageMenu,
    MealTypeUsageResponse,
)
from backend.api.schemas.menu import MenuResponse, MenuSlotSchema
from backend.api.schemas.preference import PreferenceCreate, PreferenceResponse
from backend.api.schemas.product import ProductCreate, ProductResponse
from backend.api.schemas.recipe import (
    CookingStepSchema,
    RecipeCreate,
    RecipeIngredientSchema,
    RecipeResponse,
)
from backend.api.schemas.shopping_list import (
    MoneySchema,
    QuantitySchema,
    SavedShoppingListItemInput,
    SavedShoppingListItemSchema,
    SavedShoppingListMetaResponse,
    SavedShoppingListResponse,
    ShoppingListItemResponse,
    ShoppingListResponse,
)
from backend.application.use_cases.generate_meal_summary import (
    MealSummaryResponse as MealSummaryDomain,
)
from backend.application.use_cases.manage_family import FamilyMemberData
from backend.application.use_cases.manage_preference import PreferenceData
from backend.application.use_cases.manage_product import ProductData
from backend.application.use_cases.manage_recipe import RecipeData
from backend.application.use_cases.manage_saved_shopping_list import (
    SavedShoppingListItemData,
)
from backend.domain.entities.family_member import FamilyMember
from backend.domain.entities.meal_type import MealType
from backend.domain.entities.menu import MenuSlot, WeeklyMenu
from backend.domain.entities.preference import Preference
from backend.domain.entities.product import Product
from backend.domain.entities.recipe import Recipe
from backend.domain.entities.saved_shopping_list import (
    SavedShoppingList,
    SavedShoppingListItem,
)
from backend.domain.entities.shopping_list import ShoppingList, ShoppingListItem
from backend.domain.services.shopping_list_builder import IngredientNode
from backend.domain.value_objects.category import ActiveCategory, Category
from backend.domain.value_objects.cooking_step import CookingStep
from backend.domain.value_objects.money import Money
from backend.domain.value_objects.preference_enums import PreferenceMode, PreferenceType
from backend.domain.value_objects.quantity import Quantity
from backend.domain.value_objects.recipe_ingredient import RecipeIngredient
from backend.domain.value_objects.types import (
    FamilyMemberId,
    MealTypeId,
    PreferenceId,
    ProductCategoryId,
    ProductId,
    RecipeCategoryId,
    RecipeId,
)

# ── Preference ──────────────────────────────────────────────────────

def preference_to_response(pref: Preference) -> PreferenceResponse:
    return PreferenceResponse(
        id=int(pref.id),
        name=pref.name,
        type=pref.type.value,
        mode=pref.mode.value,
        category_ids=[int(cid) for cid in pref.category_ids],
        product_ids=[int(pid) for pid in pref.product_ids],
        recipe_category_ids=[int(rcid) for rcid in pref.recipe_category_ids],
    )


def schema_to_preference_data(body: PreferenceCreate) -> PreferenceData:
    return PreferenceData(
        name=body.name,
        type=PreferenceType(body.type),
        mode=PreferenceMode(body.mode),
        category_ids=[ProductCategoryId(cid) for cid in body.category_ids],
        product_ids=[ProductId(pid) for pid in body.product_ids],
        recipe_category_ids=[RecipeCategoryId(rcid) for rcid in body.recipe_category_ids],
    )

# ── Recipe ─────────────────────────────────────────────────────────

def recipe_to_response(
    recipe: Recipe,
    sub_recipe_name_lookup: Callable[[RecipeId], str | None] | None = None,
) -> RecipeResponse:
    ingredients = []
    for ing in recipe.ingredients:
        sub_name: str | None = None
        if ing.is_sub_recipe and sub_recipe_name_lookup is not None:
            assert ing.sub_recipe_id is not None
            sub_name = sub_recipe_name_lookup(ing.sub_recipe_id)
        ingredients.append(RecipeIngredientSchema(
            product_id=int(ing.product_id) if ing.product_id is not None else None,
            sub_recipe_id=int(ing.sub_recipe_id) if ing.sub_recipe_id is not None else None,
            sub_recipe_name=sub_name,
            quantity_amount=ing.quantity.amount,
            quantity_unit=ing.quantity.unit,
            order=ing.order,
        ))
    return RecipeResponse(
        id=int(recipe.id),
        name=recipe.name,
        category_id=int(recipe.category_id),
        servings=recipe.servings,
        ingredients=ingredients,
        steps=[
            CookingStepSchema(order=s.order, description=s.description)
            for s in recipe.steps
        ],
        weight=recipe.weight,
        total_pieces=recipe.total_pieces,
        pieces_per_portion=recipe.pieces_per_portion,
        link=recipe.link,
        comment=recipe.comment,
    )


# ── Product ────────────────────────────────────────────────────────

def product_to_response(product: Product) -> ProductResponse:
    return ProductResponse(
        id=int(product.id),
        name=product.name,
        category_id=int(product.category_id),
        recipe_unit=product.recipe_unit,
        purchase_unit=product.purchase_unit,
        price_amount=product.price_per_purchase_unit.amount,
        price_currency=product.price_per_purchase_unit.currency,
        brand=product.brand,
        supplier=product.supplier,
        conversion_factor=product.conversion_factor,
    )


# ── Menu ───────────────────────────────────────────────────────────

def menu_slot_to_schema(slot: MenuSlot) -> MenuSlotSchema:
    return MenuSlotSchema(
        day=slot.day,
        meal_type_id=int(slot.meal_type_id),
        recipe_id=int(slot.recipe_id) if slot.recipe_id is not None else None,
        product_id=int(slot.product_id) if slot.product_id is not None else None,
        quantity=slot.quantity,
        unit=slot.unit,
        servings_override=slot.servings_override,
        pieces_override=slot.pieces_override,
        position=slot.position,
        member_ids=[int(mid) for mid in slot.member_ids],
    )


def menu_to_response(menu: WeeklyMenu) -> MenuResponse:
    return MenuResponse(
        id=int(menu.id),
        name=menu.name,
        slots=[menu_slot_to_schema(s) for s in menu.slots],
    )


# ── Family ─────────────────────────────────────────────────────────

def family_member_to_response(member: FamilyMember) -> FamilyMemberResponse:
    return FamilyMemberResponse(
        id=int(member.id),
        name=member.name,
        portion_multiplier=member.portion_multiplier,
        comment=member.comment,
        preference_ids=[int(pid) for pid in member.preference_ids],
    )


# ── Category ───────────────────────────────────────────────────────

def category_to_response(cat: Category) -> CategoryResponse:
    return CategoryResponse(id=cat.id, name=cat.name, active=cat.active, color=cat.color)


def active_category_to_response(cat: ActiveCategory) -> ActiveCategoryResponse:
    return ActiveCategoryResponse(id=cat.id, name=cat.name, color=cat.color)


# ── Shopping List ──────────────────────────────────────────────────

def money_to_schema(money: Money) -> MoneySchema:
    return MoneySchema(amount=money.amount, currency=money.currency)


def quantity_to_schema(qty: Quantity) -> QuantitySchema:
    return QuantitySchema(amount=qty.amount, unit=qty.unit)


def shopping_item_to_response(item: ShoppingListItem) -> ShoppingListItemResponse:
    return ShoppingListItemResponse(
        product_id=int(item.product_id),
        product_name=item.product_name,
        category=item.category,
        quantity=quantity_to_schema(item.quantity),
        buy_quantity=quantity_to_schema(item.buy_quantity),
        cost=money_to_schema(item.cost),
        purchased=item.purchased,
        recipe_quantity=(
            quantity_to_schema(item.recipe_quantity)
            if item.recipe_quantity is not None
            else None
        ),
    )


def shopping_list_to_response(sl: ShoppingList) -> ShoppingListResponse:
    return ShoppingListResponse(
        items=[shopping_item_to_response(item) for item in sl.items],
        total_cost=money_to_schema(sl.total_cost()),
    )


def saved_shopping_item_to_schema(item: SavedShoppingListItem) -> SavedShoppingListItemSchema:
    return SavedShoppingListItemSchema(
        id=int(item.id),
        product_id=int(item.product_id) if item.product_id is not None else None,
        product_name=item.product_name,
        category=item.category,
        quantity=quantity_to_schema(item.quantity),
        buy_quantity=quantity_to_schema(item.buy_quantity),
        buy_quantity_overridden=item.buy_quantity_overridden,
        cost=money_to_schema(item.cost),
        purchased=item.purchased,
        recipe_quantity=(
            quantity_to_schema(item.recipe_quantity)
            if item.recipe_quantity is not None
            else None
        ),
        item_order=item.item_order,
    )


def saved_shopping_list_to_response(sl: SavedShoppingList) -> SavedShoppingListResponse:
    return SavedShoppingListResponse(
        id=int(sl.id),
        name=sl.name,
        items=[saved_shopping_item_to_schema(item) for item in sl.items],
        total_cost=money_to_schema(sl.total_cost()),
        source_menu_id=int(sl.source_menu_id) if sl.source_menu_id is not None else None,
        created_at=sl.created_at.isoformat(),
        updated_at=sl.updated_at.isoformat(),
    )


def saved_shopping_list_to_meta(sl: SavedShoppingList) -> SavedShoppingListMetaResponse:
    return SavedShoppingListMetaResponse(
        id=int(sl.id),
        name=sl.name,
        source_menu_id=int(sl.source_menu_id) if sl.source_menu_id is not None else None,
        created_at=sl.created_at.isoformat(),
        updated_at=sl.updated_at.isoformat(),
    )


def schema_to_saved_shopping_list_item_data(
    item: SavedShoppingListItemInput,
) -> SavedShoppingListItemData:
    return SavedShoppingListItemData(
        product_id=item.product_id,
        product_name=item.product_name,
        category=item.category,
        quantity_amount=item.quantity_amount,
        quantity_unit=item.quantity_unit,
        buy_quantity_amount=item.buy_quantity_amount,
        buy_quantity_unit=item.buy_quantity_unit,
        buy_quantity_overridden=item.buy_quantity_overridden,
        cost_amount=item.cost_amount,
        cost_currency=item.cost_currency,
        purchased=item.purchased,
        recipe_quantity_amount=item.recipe_quantity_amount,
        recipe_quantity_unit=item.recipe_quantity_unit,
        item_order=item.item_order,
    )


# ── Schema → Domain Data ─────────────────────────────────────────

def schema_to_recipe_data(body: RecipeCreate) -> RecipeData:
    ingredients = []
    for ing in body.ingredients:
        ingredients.append(RecipeIngredient(
            product_id=ProductId(ing.product_id) if ing.product_id is not None else None,
            sub_recipe_id=RecipeId(ing.sub_recipe_id) if ing.sub_recipe_id is not None else None,
            quantity=Quantity(ing.quantity_amount, ing.quantity_unit),
            order=ing.order,
        ))
    return RecipeData(
        name=body.name,
        category_id=RecipeCategoryId(body.category_id),
        servings=body.servings,
        ingredients=ingredients,
        steps=[
            CookingStep(order=s.order, description=s.description)
            for s in body.steps
        ],
        weight=body.weight,
        total_pieces=body.total_pieces,
        pieces_per_portion=body.pieces_per_portion,
        link=body.link,
        comment=body.comment,
    )


def schema_to_product_data(body: ProductCreate) -> ProductData:
    return ProductData(
        name=body.name,
        category_id=ProductCategoryId(body.category_id),
        recipe_unit=body.recipe_unit,
        purchase_unit=body.purchase_unit,
        price=Money(body.price_amount, body.price_currency),
        brand=body.brand,
        supplier=body.supplier,
        conversion_factor=body.conversion_factor,
    )


def schema_to_family_data(body: FamilyMemberCreate) -> FamilyMemberData:
    return FamilyMemberData(
        name=body.name,
        portion_multiplier=body.portion_multiplier,
        comment=body.comment,
        preference_ids=[PreferenceId(pid) for pid in body.preference_ids],
    )


def schema_to_menu_slot(s: MenuSlotSchema) -> MenuSlot:
    return MenuSlot(
        day=s.day,
        meal_type_id=MealTypeId(s.meal_type_id),
        recipe_id=RecipeId(s.recipe_id) if s.recipe_id is not None else None,
        product_id=ProductId(s.product_id) if s.product_id is not None else None,
        quantity=s.quantity,
        unit=s.unit,
        servings_override=s.servings_override,
        pieces_override=s.pieces_override,
        position=s.position,
        member_ids=[FamilyMemberId(mid) for mid in s.member_ids],
    )


# ── Meal Summary ──────────────────────────────────────────────────

def _ingredient_node_to_schema(node: IngredientNode) -> MealIngredientSchema:
    return MealIngredientSchema(
        product_id=int(node.product_id) if node.product_id is not None else None,
        product_name=node.product_name,
        quantity_amount=node.quantity_amount,
        quantity_unit=node.quantity_unit,
        sub_recipe_id=int(node.sub_recipe_id) if node.sub_recipe_id is not None else None,
        sub_recipe_name=node.sub_recipe_name,
        sub_ingredients=[_ingredient_node_to_schema(c) for c in node.children],
    )


# ── MealType ──────────────────────────────────────────────────────

def meal_type_to_response(mt: MealType) -> MealTypeResponse:
    return MealTypeResponse(
        id=int(mt.id),
        name=mt.name,
        time=mt.time.strftime("%H:%M"),
        is_system=mt.is_system,
        sort_order=mt.sort_order,
    )


def meal_type_usage_to_response(
    meal_type_id: int, menus: list[tuple[int, str]]
) -> MealTypeUsageResponse:
    return MealTypeUsageResponse(
        meal_type_id=meal_type_id,
        menus=[MealTypeUsageMenu(id=mid, name=mname) for mid, mname in menus],
        count=len(menus),
    )


def meal_summary_to_response(summary: MealSummaryDomain) -> MealSummaryResponseSchema:
    recipes = []
    for r in summary.recipes:
        pieces = None
        if r.pieces_info is not None:
            pieces = PiecesInfoSchema(
                total_pieces=r.pieces_info["total_pieces"],
                pieces_per_portion=r.pieces_info["pieces_per_portion"],
            )
        recipes.append(MealSummaryRecipeSchema(
            recipe_id=int(r.recipe_id),
            recipe_name=r.recipe_name,
            occurrences=[
                MealOccurrenceSchema(
                    day=o.day,
                    meal_type_id=o.meal_type_id,
                    servings=o.servings,
                    pieces_override=o.pieces_override,
                    slot_index=o.slot_index,
                )
                for o in r.occurrences
            ],
            total_servings=r.total_servings,
            pieces_info=pieces,
            ingredients=[_ingredient_node_to_schema(n) for n in r.ingredients],
        ))

    products = []
    for p in summary.products:
        products.append(MealSummaryProductSchema(
            product_id=int(p.product_id),
            product_name=p.product_name,
            occurrences=[
                MealSummaryProductOccurrence(
                    day=o["day"],
                    meal_type_id=o["meal_type_id"],
                    quantity=o["quantity"],
                    unit=o["unit"],
                    slot_index=o["slot_index"],
                )
                for o in p.occurrences
            ],
            total_quantity=p.total_quantity,
            unit=p.unit,
        ))

    return MealSummaryResponseSchema(
        menu_id=int(summary.menu_id),
        menu_name=summary.menu_name,
        recipes=recipes,
        products=products,
    )
