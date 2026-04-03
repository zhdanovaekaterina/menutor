from pydantic import BaseModel, Field


class MealTypeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    time: str = Field(..., pattern=r"^([01]\d|2[0-3]):([0-5]\d)$")


class MealTypeUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    time: str = Field(..., pattern=r"^([01]\d|2[0-3]):([0-5]\d)$")


class MealTypeResponse(BaseModel):
    id: int
    name: str
    time: str
    is_system: bool
    sort_order: int


class MealTypeUsageMenu(BaseModel):
    id: int
    name: str


class MealTypeUsageResponse(BaseModel):
    meal_type_id: int
    menus: list[MealTypeUsageMenu]
    count: int
