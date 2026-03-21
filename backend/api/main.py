"""FastAPI-приложение — HTTP-адаптер поверх существующих use cases."""

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api.routers import auth, categories, family
from backend.api.routers import import_export as import_export_router
from backend.api.routers import menus, products, recipes
from backend.api.routers import shopping_list as shopping_list_router
from backend.api.routers import system
from backend.composition_root import ApplicationContainer
from backend.domain.exceptions import (
    AppError,
    AuthenticationError,
    CircularDependencyError,
    DomainError,
    EntityNotFoundError,
    ImportValidationError,
    NestingDepthExceededError,
    RepositoryError,
    UserAlreadyExistsError,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.container = ApplicationContainer()
    yield


app = FastAPI(
    title="Menutor API",
    description="API планировщика меню",
    version=_version_file.read_text().strip() if (_version_file := Path(__file__).parents[2] / "VERSION").exists() else os.environ.get("VERSION", "unknown"),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def rollback_on_error(request: Request, call_next):  # type: ignore[no-untyped-def]
    try:
        response = await call_next(request)
        return response
    except Exception:
        container = getattr(request.app.state, "container", None)
        if container is not None:
            session = getattr(container, "_session", None)
            if session is not None:
                session.rollback()
        raise


# ── Exception handlers ────────────────────────────────────────────


@app.exception_handler(AuthenticationError)
async def authentication_error_handler(
    request: Request, exc: AuthenticationError
) -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content={"detail": str(exc)},
        headers={"WWW-Authenticate": "Bearer"},
    )


@app.exception_handler(UserAlreadyExistsError)
async def user_exists_handler(
    request: Request, exc: UserAlreadyExistsError
) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(EntityNotFoundError)
async def entity_not_found_handler(
    request: Request, exc: EntityNotFoundError
) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(CircularDependencyError)
async def handle_circular_dep(request: Request, exc: CircularDependencyError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc), "error_type": "circular_dependency"},
    )


@app.exception_handler(NestingDepthExceededError)
async def handle_nesting_depth(request: Request, exc: NestingDepthExceededError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc), "error_type": "nesting_depth_exceeded"},
    )


@app.exception_handler(DomainError)
async def domain_error_handler(
    request: Request, exc: DomainError
) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(RepositoryError)
async def repository_error_handler(
    request: Request, exc: RepositoryError
) -> JSONResponse:
    return JSONResponse(status_code=500, content={"detail": str(exc)})


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(ImportValidationError)
async def import_validation_handler(
    request: Request, exc: ImportValidationError
) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(exc)})


# ── Routers ────────────────────────────────────────────────────────

app.include_router(auth.router, prefix="/api")
app.include_router(recipes.router, prefix="/api")
app.include_router(products.router, prefix="/api")
app.include_router(menus.router, prefix="/api")
app.include_router(family.router, prefix="/api")
app.include_router(categories.router, prefix="/api")
app.include_router(shopping_list_router.router, prefix="/api")
app.include_router(import_export_router.router, prefix="/api")
app.include_router(system.router, prefix="/api")
