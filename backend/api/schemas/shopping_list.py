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
    cost: MoneySchema
    purchased: bool
    recipe_quantity: QuantitySchema | None


class ShoppingListResponse(BaseModel):
    items: list[ShoppingListItemResponse]
    total_cost: MoneySchema
