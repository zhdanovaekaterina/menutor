from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import Response

from backend.api.auth import get_current_user
from backend.api.deps import get_container
from backend.api.schemas.import_export import ImportResultResponse
from backend.composition_root import ApplicationContainer
from backend.domain.entities.user import User

router = APIRouter(tags=["import-export"])


@router.get("/{entity_type}/export/{format}")
def export_entities(
    entity_type: str,
    format: str,
    ids: str | None = None,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> Response:
    id_list = [int(x) for x in ids.split(",")] if ids else None
    data, content_type, filename = container.export_entities.execute(
        entity_type, format, user.id, id_list,
    )
    return Response(
        content=data,
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{entity_type}/export/{format}/example")
def export_example(
    entity_type: str,
    format: str,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> Response:
    data, content_type, filename = container.export_entities.example(entity_type, format)
    return Response(
        content=data,
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/{entity_type}/import/{format}", response_model=ImportResultResponse)
def import_entities(
    entity_type: str,
    format: str,
    file: UploadFile = File(...),
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> ImportResultResponse:
    data = file.file.read()
    result = container.import_entities.execute(entity_type, format, data, user.id)
    return ImportResultResponse(
        created=result.created, updated=result.updated, errors=result.errors
    )
