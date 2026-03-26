import re

from pydantic import BaseModel, field_validator

_HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


class CategoryCreate(BaseModel):
    name: str
    color: str | None = None

    @field_validator("color")
    @classmethod
    def validate_color_format(cls, v: str | None) -> str | None:
        if v is not None and not _HEX_COLOR_RE.match(v):
            raise ValueError("Формат цвета: #RRGGBB (например, #3B82F6)")
        return v.upper() if v is not None else v


class CategoryResponse(BaseModel):
    id: int
    name: str
    active: bool
    color: str | None = None


class ActiveCategoryResponse(BaseModel):
    id: int
    name: str
    color: str | None = None


class CategoryUsedResponse(BaseModel):
    used: bool


class CategoryMoveDeleteRequest(BaseModel):
    target_category_id: int
