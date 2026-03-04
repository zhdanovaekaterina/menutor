from src.infrastructure.repositories.sqlite_product_category_repository import (
    SqliteProductCategoryRepository,
)
from src.infrastructure.repositories.sqlite_recipe_category_repository import (
    SqliteRecipeCategoryRepository,
)


def test_product_category_repo_returns_active(conn) -> None:
    repo = SqliteProductCategoryRepository(conn)
    categories = repo.find_active()
    names = [name for _, name in categories]
    assert "Сыпучие" in names
    assert "Молочные" in names
    assert "Мясо" in names


def test_product_category_repo_returns_id_name_tuples(conn) -> None:
    repo = SqliteProductCategoryRepository(conn)
    categories = repo.find_active()
    for cat_id, cat_name in categories:
        assert isinstance(cat_id, int)
        assert isinstance(cat_name, str)


def test_product_category_repo_excludes_inactive(conn) -> None:
    conn.execute(
        "INSERT INTO product_categories (name, active) VALUES ('Архив', 0)"
    )
    conn.commit()

    repo = SqliteProductCategoryRepository(conn)
    categories = repo.find_active()
    names = [name for _, name in categories]

    assert "Архив" not in names


def test_product_category_repo_sorted(conn) -> None:
    repo = SqliteProductCategoryRepository(conn)
    categories = repo.find_active()
    names = [name for _, name in categories]
    assert names == sorted(names)


def test_recipe_category_repo_returns_active(conn) -> None:
    repo = SqliteRecipeCategoryRepository(conn)
    categories = repo.find_active()
    names = [name for _, name in categories]
    assert "Завтраки" in names
    assert "Основные" in names
    assert "Салаты" in names


def test_recipe_category_repo_returns_id_name_tuples(conn) -> None:
    repo = SqliteRecipeCategoryRepository(conn)
    categories = repo.find_active()
    for cat_id, cat_name in categories:
        assert isinstance(cat_id, int)
        assert isinstance(cat_name, str)


def test_recipe_category_repo_excludes_inactive(conn) -> None:
    conn.execute(
        "INSERT INTO recipe_categories (name, active) VALUES ('Старые', 0)"
    )
    conn.commit()

    repo = SqliteRecipeCategoryRepository(conn)
    categories = repo.find_active()
    names = [name for _, name in categories]

    assert "Старые" not in names


def test_recipe_category_repo_sorted(conn) -> None:
    repo = SqliteRecipeCategoryRepository(conn)
    categories = repo.find_active()
    names = [name for _, name in categories]
    assert names == sorted(names)
