from decimal import Decimal

from pydantic import BaseModel


class QuantitySchema(BaseModel):
    amount: float
    unit: str


class MoneySchema(BaseModel):
    amount: Decimal
    currency: str


class ShoppingListItemResponse(BaseModel):
    product_id: int
    product_name: str
    category: str
    quantity: QuantitySchema
    buy_quantity: QuantitySchema
    cost: MoneySchema
    purchased: bool
    recipe_quantity: QuantitySchema | None


class ShoppingListResponse(BaseModel):
    items: list[ShoppingListItemResponse]
    total_cost: MoneySchema


# ── Saved Shopping List ────────────────────────────────────────────


class SavedShoppingListItemSchema(BaseModel):
    """Item в сохраненном списке — полный набор полей для обмена."""

    id: int
    product_id: int | None
    product_name: str
    category: str
    quantity: QuantitySchema
    buy_quantity: QuantitySchema
    buy_quantity_overridden: bool
    cost: MoneySchema
    purchased: bool
    recipe_quantity: QuantitySchema | None
    item_order: int


class SavedShoppingListItemInput(BaseModel):
    """Input schema для создания/обновления item."""

    product_id: int | None = None
    product_name: str
    category: str
    quantity_amount: float
    quantity_unit: str
    buy_quantity_amount: float
    buy_quantity_unit: str
    buy_quantity_overridden: bool = False
    cost_amount: float
    cost_currency: str = "RUB"
    purchased: bool = False
    recipe_quantity_amount: float | None = None
    recipe_quantity_unit: str | None = None
    item_order: int = 0


class SavedShoppingListResponse(BaseModel):
    """Полный ответ с items."""

    id: int
    name: str
    items: list[SavedShoppingListItemSchema]
    total_cost: MoneySchema
    source_menu_id: int | None
    created_at: str  # ISO 8601
    updated_at: str


class SavedShoppingListMetaResponse(BaseModel):
    """Meta без items — для списка в боковой панели."""

    id: int
    name: str
    source_menu_id: int | None
    created_at: str
    updated_at: str


class UpdateSavedShoppingListRequest(BaseModel):
    """PUT request body."""

    name: str
    items: list[SavedShoppingListItemInput]


class RenameSavedShoppingListRequest(BaseModel):
    """PATCH request body."""

    name: str
