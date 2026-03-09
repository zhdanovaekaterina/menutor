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


# ── CRUD tests ─────────────────────────────────────────────────────────


def test_product_category_find_all_includes_inactive(conn) -> None:
    conn.execute(
        "INSERT INTO product_categories (name, active) VALUES ('Архив', 0)"
    )
    conn.commit()

    repo = SqliteProductCategoryRepository(conn)
    categories = repo.find_all()
    names = [name for _, name, _ in categories]
    assert "Архив" in names

    archived = [(cid, n, a) for cid, n, a in categories if n == "Архив"]
    assert archived[0][2] is False


def test_product_category_save_creates_new(conn) -> None:
    repo = SqliteProductCategoryRepository(conn)
    new_id = repo.save("Замороженные")
    assert isinstance(new_id, int)
    names = [name for _, name in repo.find_active()]
    assert "Замороженные" in names


def test_product_category_save_updates_existing(conn) -> None:
    repo = SqliteProductCategoryRepository(conn)
    new_id = repo.save("Тестовая")
    repo.save("Тестовая (изм.)", new_id)
    names = [name for _, name in repo.find_active()]
    assert "Тестовая (изм.)" in names
    assert "Тестовая" not in names


def test_product_category_delete_makes_inactive(conn) -> None:
    repo = SqliteProductCategoryRepository(conn)
    new_id = repo.save("Удаляемая")
    repo.delete(new_id)
    active_names = [name for _, name in repo.find_active()]
    assert "Удаляемая" not in active_names

    all_names = [name for _, name, _ in repo.find_all()]
    assert "Удаляемая" in all_names


def test_product_category_is_used_false(conn) -> None:
    repo = SqliteProductCategoryRepository(conn)
    new_id = repo.save("Пустая")
    assert repo.is_used(new_id) is False


def test_product_category_is_used_true(conn) -> None:
    repo = SqliteProductCategoryRepository(conn)
    new_id = repo.save("С продуктами")
    conn.execute(
        "INSERT INTO products (name, category_id, recipe_unit, purchase_unit) "
        "VALUES ('Тест', ?, 'g', 'kg')",
        (new_id,),
    )
    conn.commit()
    assert repo.is_used(new_id) is True


def test_recipe_category_find_all_includes_inactive(conn) -> None:
    conn.execute(
        "INSERT INTO recipe_categories (name, active) VALUES ('Старые', 0)"
    )
    conn.commit()

    repo = SqliteRecipeCategoryRepository(conn)
    categories = repo.find_all()
    names = [name for _, name, _ in categories]
    assert "Старые" in names

    archived = [(cid, n, a) for cid, n, a in categories if n == "Старые"]
    assert archived[0][2] is False


def test_recipe_category_save_creates_new(conn) -> None:
    repo = SqliteRecipeCategoryRepository(conn)
    new_id = repo.save("Выпечка")
    assert isinstance(new_id, int)
    names = [name for _, name in repo.find_active()]
    assert "Выпечка" in names


def test_recipe_category_save_updates_existing(conn) -> None:
    repo = SqliteRecipeCategoryRepository(conn)
    new_id = repo.save("Тестовая")
    repo.save("Тестовая (изм.)", new_id)
    names = [name for _, name in repo.find_active()]
    assert "Тестовая (изм.)" in names
    assert "Тестовая" not in names


def test_recipe_category_delete_makes_inactive(conn) -> None:
    repo = SqliteRecipeCategoryRepository(conn)
    new_id = repo.save("Удаляемая")
    repo.delete(new_id)
    active_names = [name for _, name in repo.find_active()]
    assert "Удаляемая" not in active_names

    all_names = [name for _, name, _ in repo.find_all()]
    assert "Удаляемая" in all_names


def test_recipe_category_is_used_false(conn) -> None:
    repo = SqliteRecipeCategoryRepository(conn)
    new_id = repo.save("Пустая")
    assert repo.is_used(new_id) is False


def test_recipe_category_is_used_true(conn) -> None:
    repo = SqliteRecipeCategoryRepository(conn)
    new_id = repo.save("С рецептами")
    conn.execute(
        "INSERT INTO recipes (name, category_id, servings) VALUES ('Тест', ?, 1)",
        (new_id,),
    )
    conn.commit()
    assert repo.is_used(new_id) is True


def test_product_category_save_reactivates_on_edit(conn) -> None:
    """Editing an inactive category should reactivate it."""
    repo = SqliteProductCategoryRepository(conn)
    new_id = repo.save("Скрытая")
    repo.delete(new_id)
    assert "Скрытая" not in [name for _, name in repo.find_active()]

    repo.save("Скрытая (восст.)", new_id)
    active_names = [name for _, name in repo.find_active()]
    assert "Скрытая (восст.)" in active_names


def test_recipe_category_save_reactivates_on_edit(conn) -> None:
    """Editing an inactive category should reactivate it."""
    repo = SqliteRecipeCategoryRepository(conn)
    new_id = repo.save("Скрытая")
    repo.delete(new_id)
    assert "Скрытая" not in [name for _, name in repo.find_active()]

    repo.save("Скрытая (восст.)", new_id)
    active_names = [name for _, name in repo.find_active()]
    assert "Скрытая (восст.)" in active_names
