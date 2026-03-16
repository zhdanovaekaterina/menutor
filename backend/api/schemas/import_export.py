from pydantic import BaseModel


class ImportResultResponse(BaseModel):
    created: int
    updated: int
    errors: list[str]
