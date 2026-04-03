from pydantic import BaseModel


class PreferenceCreate(BaseModel):
    name: str
    type: str          # "CATEGORY_BASED" or "ALLERGY"
    mode: str          # "BLOCKED" or "ALLOWED"
    category_ids: list[int] = []
    product_ids: list[int] = []
    recipe_category_ids: list[int] = []


PreferenceUpdate = PreferenceCreate


class PreferenceResponse(BaseModel):
    id: int
    name: str
    type: str
    mode: str
    category_ids: list[int]
    product_ids: list[int]
    recipe_category_ids: list[int]


class PreferenceMatchResponse(BaseModel):
    """List of preferences that a recipe matches."""
    preferences: list[PreferenceResponse]
