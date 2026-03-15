from fastapi import APIRouter, Depends, status

from backend.api.auth import get_current_user
from backend.api.converters import family_member_to_response, schema_to_family_data
from backend.api.deps import get_container
from backend.api.schemas.family import (
    FamilyMemberCreate,
    FamilyMemberResponse,
    FamilyMemberUpdate,
)
from backend.composition_root import ApplicationContainer
from backend.domain.entities.user import User
from backend.domain.value_objects.types import FamilyMemberId

router = APIRouter(prefix="/family-members", tags=["family"])


@router.get("", response_model=list[FamilyMemberResponse])
def list_family_members(
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> list[FamilyMemberResponse]:
    members = container.list_family_members.execute(user.id)
    return [family_member_to_response(m) for m in members]


@router.post(
    "", response_model=FamilyMemberResponse, status_code=status.HTTP_201_CREATED
)
def create_family_member(
    body: FamilyMemberCreate,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> FamilyMemberResponse:
    data = schema_to_family_data(body)
    member = container.create_family_member.execute(data, user.id)
    return family_member_to_response(member)


@router.put("/{member_id}", response_model=FamilyMemberResponse)
def update_family_member(
    member_id: int,
    body: FamilyMemberUpdate,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> FamilyMemberResponse:
    data = schema_to_family_data(body)
    member = container.edit_family_member.execute(
        FamilyMemberId(member_id), data, user.id
    )
    return family_member_to_response(member)


@router.delete("/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_family_member(
    member_id: int,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> None:
    container.delete_family_member.execute(FamilyMemberId(member_id), user.id)
