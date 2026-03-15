from decimal import Decimal

from pydantic import BaseModel


class ProductCreate(BaseModel):
    name: str
    category_id: int
    recipe_unit: str
    purchase_unit: str
    price_amount: Decimal
    price_currency: str = "RUB"
    brand: str = ""
    supplier: str = ""
    conversion_factor: float = 1.0


ProductUpdate = ProductCreate


class PriceUpdate(BaseModel):
    amount: Decimal
    currency: str = "RUB"


class ProductResponse(BaseModel):
    id: int
    name: str
    category_id: int
    recipe_unit: str
    purchase_unit: str
    price_amount: Decimal
    price_currency: str
    brand: str
    supplier: str
    conversion_factor: float
