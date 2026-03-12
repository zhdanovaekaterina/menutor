from fastapi import APIRouter

from backend.api.schemas.system import OkResponse

router = APIRouter(tags=["system"])


@router.get("/ping", response_model=OkResponse)
def list_recipes() -> OkResponse:
    return OkResponse()
