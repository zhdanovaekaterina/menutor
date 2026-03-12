"""FastAPI-приложение — HTTP-адаптер поверх существующих use cases."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api.routers import auth, categories, family, menus, products, recipes, system
from backend.api.routers import shopping_list as shopping_list_router
from backend.composition_root import ApplicationContainer
from backend.domain.exceptions import (
    AppError,
    AuthenticationError,
    DomainError,
    EntityNotFoundError,
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
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


# ── Routers ────────────────────────────────────────────────────────

app.include_router(auth.router, prefix="/api")
app.include_router(recipes.router, prefix="/api")
app.include_router(products.router, prefix="/api")
app.include_router(menus.router, prefix="/api")
app.include_router(family.router, prefix="/api")
app.include_router(categories.router, prefix="/api")
app.include_router(shopping_list_router.router, prefix="/api")
app.include_router(system.router, prefix="/api")
