from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.auth import get_current_user
from backend.api.converters import preference_to_response, schema_to_preference_data
from backend.api.deps import get_container
from backend.api.schemas.preference import (
    PreferenceCreate,
    PreferenceResponse,
    PreferenceUpdate,
)
from backend.composition_root import ApplicationContainer
from backend.domain.entities.user import User
from backend.domain.value_objects.types import PreferenceId

router = APIRouter(prefix="/preferences", tags=["preferences"])


@router.get("", response_model=list[PreferenceResponse])
def list_preferences(
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> list[PreferenceResponse]:
    prefs = container.list_preferences.execute(user.id)
    return [preference_to_response(p) for p in prefs]


@router.get("/{preference_id}", response_model=PreferenceResponse)
def get_preference(
    preference_id: int,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> PreferenceResponse:
    pref = container.get_preference.execute(PreferenceId(preference_id), user.id)
    if pref is None:
        raise HTTPException(status_code=404, detail="Предпочтение не найдено")
    return preference_to_response(pref)


@router.post(
    "", response_model=PreferenceResponse, status_code=status.HTTP_201_CREATED
)
def create_preference(
    body: PreferenceCreate,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> PreferenceResponse:
    data = schema_to_preference_data(body)
    pref = container.create_preference.execute(data, user.id)
    return preference_to_response(pref)


@router.put("/{preference_id}", response_model=PreferenceResponse)
def update_preference(
    preference_id: int,
    body: PreferenceUpdate,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> PreferenceResponse:
    data = schema_to_preference_data(body)
    pref = container.update_preference.execute(
        PreferenceId(preference_id), data, user.id
    )
    return preference_to_response(pref)


@router.delete("/{preference_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_preference(
    preference_id: int,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> None:
    container.delete_preference.execute(PreferenceId(preference_id), user.id)
