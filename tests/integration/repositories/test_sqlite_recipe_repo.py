from decimal import Decimal

import pytest

from backend.domain.entities.product import Product
from backend.domain.entities.recipe import Recipe
from backend.domain.value_objects.cooking_step import CookingStep
from backend.domain.value_objects.money import Money
from backend.domain.value_objects.quantity import Quantity
from backend.domain.value_objects.recipe_ingredient import RecipeIngredient
from backend.domain.value_objects.types import (
    ProductCategoryId,
    ProductId,
    RecipeCategoryId,
    RecipeId,
    UserId,
)
from backend.infrastructure.repositories.sqlite_product_repository import (
    SqliteProductRepository,
)
from backend.infrastructure.repositories.sqlite_recipe_repository import (
    SqliteRecipeRepository,
)


@pytest.fixture
def product_repo(conn: object) -> SqliteProductRepository:
    return SqliteProductRepository(conn)  # type: ignore[arg-type]


@pytest.fixture
def recipe_repo(conn: object) -> SqliteRecipeRepository:
    return SqliteRecipeRepository(conn)  # type: ignore[arg-type]


@pytest.fixture
def flour(product_repo: SqliteProductRepository, user_id: UserId) -> Product:
    return product_repo.save(Product(
        id=ProductId(0), name="Мука",
        recipe_unit="g", purchase_unit="kg",
        price_per_purchase_unit=Money(Decimal("80")),
        conversion_factor=1000,
        category_id=ProductCategoryId(1),
        user_id=user_id,
    ))


def _pancake_recipe(flour_id: ProductId, user_id: UserId) -> Recipe:
    return Recipe(
        id=RecipeId(0),
        name="Блины",
        servings=4,
        ingredients=[RecipeIngredient(flour_id, Quantity(200.0, "g"))],
        steps=[CookingStep(1, "Смешать"), CookingStep(2, "Пожарить")],
        category_id=RecipeCategoryId(1),  # Завтраки
        user_id=user_id,
    )


def test_save_assigns_id(recipe_repo: SqliteRecipeRepository,
                          flour: Product, user_id: UserId) -> None:
    saved = recipe_repo.save(_pancake_recipe(flour.id, user_id))
    assert saved.id != RecipeId(0)


def test_save_and_get_by_id_full_roundtrip(recipe_repo: SqliteRecipeRepository,
                                            flour: Product, user_id: UserId) -> None:
    saved = recipe_repo.save(_pancake_recipe(flour.id, user_id))
    retrieved = recipe_repo.get_by_id(saved.id)

    assert retrieved is not None
    assert retrieved.name == "Блины"
    assert retrieved.category_id == RecipeCategoryId(1)
    assert retrieved.servings == 4
    assert retrieved.user_id == user_id
    assert len(retrieved.ingredients) == 1
    assert retrieved.ingredients[0].product_id == flour.id
    assert retrieved.ingredients[0].quantity == Quantity(200.0, "g")

    assert len(retrieved.steps) == 2
    assert retrieved.steps[0].order == 1
    assert retrieved.steps[0].description == "Смешать"
    assert retrieved.steps[1].order == 2


def test_get_by_id_returns_none_when_absent(recipe_repo: SqliteRecipeRepository) -> None:
    assert recipe_repo.get_by_id(RecipeId(9999)) is None


def test_delete_removes_recipe(recipe_repo: SqliteRecipeRepository,
                                flour: Product, user_id: UserId) -> None:
    saved = recipe_repo.save(_pancake_recipe(flour.id, user_id))
    recipe_repo.delete(saved.id)
    assert recipe_repo.get_by_id(saved.id) is None


def test_delete_cascades_to_ingredients_and_steps(recipe_repo: SqliteRecipeRepository,
                                                   flour: Product,
                                                   conn: object, user_id: UserId) -> None:
    from sqlalchemy import text
    from sqlalchemy.orm import Session
    session: Session = conn  # type: ignore[assignment]
    saved = recipe_repo.save(_pancake_recipe(flour.id, user_id))
    recipe_repo.delete(saved.id)

    ing_count = session.execute(
        text("SELECT COUNT(*) FROM recipe_ingredients WHERE recipe_id = :id"),
        {"id": saved.id},
    ).scalar()
    step_count = session.execute(
        text("SELECT COUNT(*) FROM cooking_steps WHERE recipe_id = :id"),
        {"id": saved.id},
    ).scalar()
    assert ing_count == 0
    assert step_count == 0


def test_find_by_category_id(recipe_repo: SqliteRecipeRepository,
                              flour: Product, user_id: UserId) -> None:
    recipe_repo.save(_pancake_recipe(flour.id, user_id))
    recipe_repo.save(Recipe(id=RecipeId(0), name="Котлеты", servings=4,
                            category_id=RecipeCategoryId(2), user_id=user_id))

    breakfast = recipe_repo.find_by_category_id(RecipeCategoryId(1), user_id)
    assert len(breakfast) == 1
    assert breakfast[0].name == "Блины"


def test_find_all(recipe_repo: SqliteRecipeRepository,
                  flour: Product, user_id: UserId) -> None:
    recipe_repo.save(_pancake_recipe(flour.id, user_id))
    recipe_repo.save(Recipe(id=RecipeId(0), name="Котлеты", servings=4,
                            category_id=RecipeCategoryId(2), user_id=user_id))
    assert len(recipe_repo.find_all(user_id)) == 2


def test_update_replaces_ingredients_and_steps(recipe_repo: SqliteRecipeRepository,
                                                flour: Product, user_id: UserId) -> None:
    saved = recipe_repo.save(_pancake_recipe(flour.id, user_id))
    updated = Recipe(
        id=saved.id,
        name="Оладьи",
        servings=6,
        ingredients=[RecipeIngredient(flour.id, Quantity(300.0, "g"))],
        steps=[CookingStep(1, "Только смешать")],
        category_id=RecipeCategoryId(1),
        user_id=user_id,
    )
    result = recipe_repo.save(updated)

    assert result.name == "Оладьи"
    assert result.servings == 6
    assert len(result.ingredients) == 1
    assert result.ingredients[0].quantity == Quantity(300.0, "g")
    assert len(result.steps) == 1
