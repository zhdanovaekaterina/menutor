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
    weight_per_piece_g: float | None = None
    conversion_factor: float = 1.0


class ProductUpdate(BaseModel):
    name: str
    category_id: int
    recipe_unit: str
    purchase_unit: str
    price_amount: Decimal
    price_currency: str = "RUB"
    brand: str = ""
    supplier: str = ""
    weight_per_piece_g: float | None = None
    conversion_factor: float = 1.0


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
    weight_per_piece_g: float | None
    conversion_factor: float
