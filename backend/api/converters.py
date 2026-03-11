"""Конвертеры между доменными объектами и Pydantic-схемами."""

from backend.api.schemas.category import ActiveCategoryResponse, CategoryResponse
from backend.api.schemas.family import FamilyMemberResponse
from backend.api.schemas.menu import MenuResponse, MenuSlotSchema
from backend.api.schemas.product import ProductResponse
from backend.api.schemas.recipe import (
    CookingStepSchema,
    RecipeIngredientSchema,
    RecipeResponse,
)
from backend.api.schemas.shopping_list import (
    MoneySchema,
    QuantitySchema,
    ShoppingListItemResponse,
    ShoppingListResponse,
)
from backend.domain.entities.family_member import FamilyMember
from backend.domain.entities.menu import MenuSlot, WeeklyMenu
from backend.domain.entities.product import Product
from backend.domain.entities.recipe import Recipe
from backend.domain.entities.shopping_list import ShoppingList, ShoppingListItem
from backend.domain.value_objects.category import ActiveCategory, Category
from backend.domain.value_objects.money import Money
from backend.domain.value_objects.quantity import Quantity


# ── Recipe ─────────────────────────────────────────────────────────

def recipe_to_response(recipe: Recipe) -> RecipeResponse:
    return RecipeResponse(
        id=int(recipe.id),
        name=recipe.name,
        category_id=int(recipe.category_id),
        servings=recipe.servings,
        ingredients=[
            RecipeIngredientSchema(
                product_id=int(ing.product_id),
                quantity_amount=ing.quantity.amount,
                quantity_unit=ing.quantity.unit,
            )
            for ing in recipe.ingredients
        ],
        steps=[
            CookingStepSchema(order=s.order, description=s.description)
            for s in recipe.steps
        ],
        weight=recipe.weight,
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
        weight_per_piece_g=product.weight_per_piece_g,
        conversion_factor=product.conversion_factor,
    )


# ── Menu ───────────────────────────────────────────────────────────

def menu_slot_to_schema(slot: MenuSlot) -> MenuSlotSchema:
    return MenuSlotSchema(
        day=slot.day,
        meal_type=slot.meal_type,
        recipe_id=int(slot.recipe_id) if slot.recipe_id is not None else None,
        product_id=int(slot.product_id) if slot.product_id is not None else None,
        quantity=slot.quantity,
        unit=slot.unit,
        servings_override=slot.servings_override,
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
        dietary_restrictions=member.dietary_restrictions,
        comment=member.comment,
    )


# ── Category ───────────────────────────────────────────────────────

def category_to_response(cat: Category) -> CategoryResponse:
    return CategoryResponse(id=cat.id, name=cat.name, active=cat.active)


def active_category_to_response(cat: ActiveCategory) -> ActiveCategoryResponse:
    return ActiveCategoryResponse(id=cat.id, name=cat.name)


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
