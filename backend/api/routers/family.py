from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.converters import family_member_to_response
from backend.api.deps import get_container
from backend.api.schemas.family import (
    FamilyMemberCreate,
    FamilyMemberResponse,
    FamilyMemberUpdate,
)
from backend.application.use_cases.manage_family import FamilyMemberData
from backend.composition_root import ApplicationContainer
from backend.domain.exceptions import EntityNotFoundError
from backend.domain.value_objects.types import FamilyMemberId

router = APIRouter(prefix="/family-members", tags=["family"])


def _to_family_data(body: FamilyMemberCreate | FamilyMemberUpdate) -> FamilyMemberData:
    return FamilyMemberData(
        name=body.name,
        portion_multiplier=body.portion_multiplier,
        dietary_restrictions=body.dietary_restrictions,
        comment=body.comment,
    )


@router.get("", response_model=list[FamilyMemberResponse])
def list_family_members(
    container: ApplicationContainer = Depends(get_container),
) -> list[FamilyMemberResponse]:
    members = container.list_family_members.execute()
    return [family_member_to_response(m) for m in members]


@router.post(
    "", response_model=FamilyMemberResponse, status_code=status.HTTP_201_CREATED
)
def create_family_member(
    body: FamilyMemberCreate,
    container: ApplicationContainer = Depends(get_container),
) -> FamilyMemberResponse:
    data = _to_family_data(body)
    member = container.create_family_member.execute(data)
    return family_member_to_response(member)


@router.put("/{member_id}", response_model=FamilyMemberResponse)
def update_family_member(
    member_id: int,
    body: FamilyMemberUpdate,
    container: ApplicationContainer = Depends(get_container),
) -> FamilyMemberResponse:
    data = _to_family_data(body)
    try:
        member = container.edit_family_member.execute(
            FamilyMemberId(member_id), data
        )
    except EntityNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    return family_member_to_response(member)


@router.delete("/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_family_member(
    member_id: int,
    container: ApplicationContainer = Depends(get_container),
) -> None:
    container.delete_family_member.execute(FamilyMemberId(member_id))
