"""Wire family member use cases."""

from typing import Any

from backend.application.use_cases.manage_family import (
    CreateFamilyMember,
    DeleteFamilyMember,
    EditFamilyMember,
    ListFamilyMembers,
)
from backend.composition._infrastructure import _Infrastructure


def _wire_family(infra: _Infrastructure) -> dict[str, Any]:
    return {
        "create_family_member": CreateFamilyMember(infra.family_repo),
        "edit_family_member": EditFamilyMember(infra.family_repo),
        "delete_family_member": DeleteFamilyMember(infra.family_repo),
        "list_family_members": ListFamilyMembers(infra.family_repo),
    }
