from datetime import time

from fastapi import APIRouter, Depends, status

from backend.api.auth import get_current_user
from backend.api.converters import meal_type_to_response, meal_type_usage_to_response
from backend.api.deps import get_container
from backend.api.schemas.meal_type import (
    MealTypeCreate,
    MealTypeResponse,
    MealTypeUpdate,
    MealTypeUsageResponse,
)
from backend.application.use_cases.manage_meal_type import MealTypeData
from backend.composition_root import ApplicationContainer
from backend.domain.entities.user import User
from backend.domain.value_objects.types import MealTypeId

router = APIRouter(prefix="/meal-types", tags=["meal-types"])


def _parse_time(time_str: str) -> time:
    h, m = time_str.split(":")
    return time(int(h), int(m))


@router.get("", response_model=list[MealTypeResponse])
def list_meal_types(
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> list[MealTypeResponse]:
    types = container.list_meal_types.execute(user.id)
    return [meal_type_to_response(mt) for mt in types]


@router.post("", response_model=MealTypeResponse, status_code=status.HTTP_201_CREATED)
def create_meal_type(
    body: MealTypeCreate,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> MealTypeResponse:
    data = MealTypeData(name=body.name, time=_parse_time(body.time))
    mt = container.create_meal_type.execute(data, user.id)
    return meal_type_to_response(mt)


@router.put("/{meal_type_id}", response_model=MealTypeResponse)
def update_meal_type(
    meal_type_id: int,
    body: MealTypeUpdate,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> MealTypeResponse:
    data = MealTypeData(name=body.name, time=_parse_time(body.time))
    mt = container.update_meal_type.execute(MealTypeId(meal_type_id), data, user.id)
    return meal_type_to_response(mt)


@router.delete("/{meal_type_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meal_type(
    meal_type_id: int,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> None:
    container.delete_meal_type.execute(MealTypeId(meal_type_id), user.id)


@router.get("/{meal_type_id}/usage", response_model=MealTypeUsageResponse)
def check_meal_type_usage(
    meal_type_id: int,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> MealTypeUsageResponse:
    menus = container.check_meal_type_usage.execute(MealTypeId(meal_type_id), user.id)
    return meal_type_usage_to_response(meal_type_id, menus)
