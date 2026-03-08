from decimal import Decimal

import pytest

from src.domain.entities.product import Product
from src.domain.entities.recipe import Recipe
from src.domain.value_objects.cooking_step import CookingStep
from src.domain.value_objects.money import Money
from src.domain.value_objects.quantity import Quantity
from src.domain.value_objects.recipe_ingredient import RecipeIngredient
from src.domain.value_objects.types import (
    ProductCategoryId,
    ProductId,
    RecipeCategoryId,
    RecipeId,
)
from src.infrastructure.repositories.sqlite_product_repository import (
    SqliteProductRepository,
)
from src.infrastructure.repositories.sqlite_recipe_repository import (
    SqliteRecipeRepository,
)


@pytest.fixture
def product_repo(conn: object) -> SqliteProductRepository:
    return SqliteProductRepository(conn)  # type: ignore[arg-type]


@pytest.fixture
def recipe_repo(conn: object) -> SqliteRecipeRepository:
    return SqliteRecipeRepository(conn)  # type: ignore[arg-type]


@pytest.fixture
def flour(product_repo: SqliteProductRepository) -> Product:
    return product_repo.save(Product(
        id=ProductId(0), name="Мука",
        recipe_unit="g", purchase_unit="kg",
        price_per_purchase_unit=Money(Decimal("80")),
        conversion_factor=0.001,
        category_id=ProductCategoryId(1),
    ))


def _pancake_recipe(flour_id: ProductId) -> Recipe:
    return Recipe(
        id=RecipeId(0),
        name="Блины",
        servings=4,
        ingredients=[RecipeIngredient(flour_id, Quantity(200.0, "g"))],
        steps=[CookingStep(1, "Смешать"), CookingStep(2, "Пожарить")],
        category_id=RecipeCategoryId(1),  # Завтраки
    )


def test_save_assigns_id(recipe_repo: SqliteRecipeRepository,
                          flour: Product) -> None:
    saved = recipe_repo.save(_pancake_recipe(flour.id))
    assert saved.id != RecipeId(0)


def test_save_and_get_by_id_full_roundtrip(recipe_repo: SqliteRecipeRepository,
                                            flour: Product) -> None:
    saved = recipe_repo.save(_pancake_recipe(flour.id))
    retrieved = recipe_repo.get_by_id(saved.id)

    assert retrieved is not None
    assert retrieved.name == "Блины"
    assert retrieved.category_id == RecipeCategoryId(1)
    assert retrieved.servings == 4
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
                                flour: Product) -> None:
    saved = recipe_repo.save(_pancake_recipe(flour.id))
    recipe_repo.delete(saved.id)
    assert recipe_repo.get_by_id(saved.id) is None


def test_delete_cascades_to_ingredients_and_steps(recipe_repo: SqliteRecipeRepository,
                                                   flour: Product,
                                                   conn: object) -> None:
    import sqlite3
    c: sqlite3.Connection = conn  # type: ignore[assignment]
    saved = recipe_repo.save(_pancake_recipe(flour.id))
    recipe_repo.delete(saved.id)

    ing_count = c.execute(
        "SELECT COUNT(*) FROM recipe_ingredients WHERE recipe_id = ?", (saved.id,)
    ).fetchone()[0]
    step_count = c.execute(
        "SELECT COUNT(*) FROM cooking_steps WHERE recipe_id = ?", (saved.id,)
    ).fetchone()[0]
    assert ing_count == 0
    assert step_count == 0


def test_find_by_category_id(recipe_repo: SqliteRecipeRepository,
                              flour: Product) -> None:
    recipe_repo.save(_pancake_recipe(flour.id))
    recipe_repo.save(Recipe(id=RecipeId(0), name="Котлеты", servings=4,
                            category_id=RecipeCategoryId(2)))

    breakfast = recipe_repo.find_by_category_id(RecipeCategoryId(1))
    assert len(breakfast) == 1
    assert breakfast[0].name == "Блины"


def test_find_all(recipe_repo: SqliteRecipeRepository,
                  flour: Product) -> None:
    recipe_repo.save(_pancake_recipe(flour.id))
    recipe_repo.save(Recipe(id=RecipeId(0), name="Котлеты", servings=4,
                            category_id=RecipeCategoryId(2)))
    assert len(recipe_repo.find_all()) == 2


def test_update_replaces_ingredients_and_steps(recipe_repo: SqliteRecipeRepository,
                                                flour: Product) -> None:
    saved = recipe_repo.save(_pancake_recipe(flour.id))
    updated = Recipe(
        id=saved.id,
        name="Оладьи",
        servings=6,
        ingredients=[RecipeIngredient(flour.id, Quantity(300.0, "g"))],
        steps=[CookingStep(1, "Только смешать")],
        category_id=RecipeCategoryId(1),
    )
    result = recipe_repo.save(updated)

    assert result.name == "Оладьи"
    assert result.servings == 6
    assert len(result.ingredients) == 1
    assert result.ingredients[0].quantity == Quantity(300.0, "g")
    assert len(result.steps) == 1
