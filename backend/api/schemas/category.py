from pydantic import BaseModel


class CategoryCreate(BaseModel):
    name: str


class CategoryResponse(BaseModel):
    id: int
    name: str
    active: bool


class ActiveCategoryResponse(BaseModel):
    id: int
    name: str


class CategoryUsedResponse(BaseModel):
    used: bool
