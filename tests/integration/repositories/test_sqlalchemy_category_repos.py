from sqlalchemy import text

from backend.infrastructure.repositories.sqlalchemy_product_category_repository import (
    SqlAlchemyProductCategoryRepository,
)
from backend.infrastructure.repositories.sqlalchemy_recipe_category_repository import (
    SqlAlchemyRecipeCategoryRepository,
)


def test_product_category_repo_returns_active(conn) -> None:
    repo = SqlAlchemyProductCategoryRepository(conn)
    categories = repo.find_active()
    names = [name for _, name in categories]
    assert "Сыпучие" in names
    assert "Молочные" in names
    assert "Мясо" in names


def test_product_category_repo_returns_id_name_tuples(conn) -> None:
    repo = SqlAlchemyProductCategoryRepository(conn)
    categories = repo.find_active()
    for cat_id, cat_name in categories:
        assert isinstance(cat_id, int)
        assert isinstance(cat_name, str)


def test_product_category_repo_excludes_inactive(conn) -> None:
    conn.execute(text(
        "INSERT INTO product_categories (name, active) VALUES ('Архив', 0)"
    ))
    conn.commit()

    repo = SqlAlchemyProductCategoryRepository(conn)
    categories = repo.find_active()
    names = [name for _, name in categories]

    assert "Архив" not in names


def test_product_category_repo_sorted(conn) -> None:
    repo = SqlAlchemyProductCategoryRepository(conn)
    categories = repo.find_active()
    names = [name for _, name in categories]
    assert names == sorted(names)


def test_recipe_category_repo_returns_active(conn) -> None:
    repo = SqlAlchemyRecipeCategoryRepository(conn)
    categories = repo.find_active()
    names = [name for _, name in categories]
    assert "Завтраки" in names
    assert "Основные" in names
    assert "Салаты" in names


def test_recipe_category_repo_returns_id_name_tuples(conn) -> None:
    repo = SqlAlchemyRecipeCategoryRepository(conn)
    categories = repo.find_active()
    for cat_id, cat_name in categories:
        assert isinstance(cat_id, int)
        assert isinstance(cat_name, str)


def test_recipe_category_repo_excludes_inactive(conn) -> None:
    conn.execute(text(
        "INSERT INTO recipe_categories (name, active) VALUES ('Старые', 0)"
    ))
    conn.commit()

    repo = SqlAlchemyRecipeCategoryRepository(conn)
    categories = repo.find_active()
    names = [name for _, name in categories]

    assert "Старые" not in names


def test_recipe_category_repo_sorted(conn) -> None:
    repo = SqlAlchemyRecipeCategoryRepository(conn)
    categories = repo.find_active()
    names = [name for _, name in categories]
    assert names == sorted(names)


# ── CRUD tests ─────────────────────────────────────────────────────────


def test_product_category_find_all_includes_inactive(conn) -> None:
    conn.execute(text(
        "INSERT INTO product_categories (name, active) VALUES ('Архив', 0)"
    ))
    conn.commit()

    repo = SqlAlchemyProductCategoryRepository(conn)
    categories = repo.find_all()
    names = [name for _, name, _ in categories]
    assert "Архив" in names

    archived = [(cid, n, a) for cid, n, a in categories if n == "Архив"]
    assert archived[0][2] is False


def test_product_category_save_creates_new(conn) -> None:
    repo = SqlAlchemyProductCategoryRepository(conn)
    new_id = repo.save("Замороженные")
    assert isinstance(new_id, int)
    names = [name for _, name in repo.find_active()]
    assert "Замороженные" in names


def test_product_category_save_updates_existing(conn) -> None:
    repo = SqlAlchemyProductCategoryRepository(conn)
    new_id = repo.save("Тестовая")
    repo.save("Тестовая (изм.)", new_id)
    names = [name for _, name in repo.find_active()]
    assert "Тестовая (изм.)" in names
    assert "Тестовая" not in names


def test_product_category_delete_makes_inactive(conn) -> None:
    repo = SqlAlchemyProductCategoryRepository(conn)
    new_id = repo.save("Удаляемая")
    repo.delete(new_id)
    active_names = [name for _, name in repo.find_active()]
    assert "Удаляемая" not in active_names

    all_names = [name for _, name, _ in repo.find_all()]
    assert "Удаляемая" in all_names


def test_product_category_hard_delete_removes_row(conn) -> None:
    repo = SqlAlchemyProductCategoryRepository(conn)
    new_id = repo.save("Удаляемая навсегда")
    repo.hard_delete(new_id)
    all_names = [name for _, name, _ in repo.find_all()]
    assert "Удаляемая навсегда" not in all_names


def test_product_category_hard_delete_removes_linked_products(conn) -> None:
    repo = SqlAlchemyProductCategoryRepository(conn)
    new_id = repo.save("С продуктами")
    conn.execute(
        text("INSERT INTO products (name, brand, supplier, category_id, recipe_unit, purchase_unit, user_id) "
             "VALUES ('Тест-продукт', '', '', :cat_id, 'g', 'kg', 1)"),
        {"cat_id": new_id},
    )
    conn.commit()
    repo.hard_delete(new_id)
    all_names = [name for _, name, _ in repo.find_all()]
    assert "С продуктами" not in all_names
    count = conn.execute(
        text("SELECT COUNT(*) FROM products WHERE category_id = :cat_id"),
        {"cat_id": new_id},
    ).scalar()
    assert count == 0


def test_product_category_hard_delete_cascades_to_recipe_ingredients(conn) -> None:
    """Hard-deleting a product category must also remove recipe_ingredients
    and menu_slots that reference the deleted products."""
    repo = SqlAlchemyProductCategoryRepository(conn)
    cat_id = repo.save("Каскад")

    # Create a product in this category
    conn.execute(
        text("INSERT INTO products (id, name, brand, supplier, category_id, "
             "recipe_unit, purchase_unit, user_id) "
             "VALUES (9000, 'Каскад-продукт', '', '', :cat_id, 'g', 'kg', 1)"),
        {"cat_id": cat_id},
    )
    # Create a recipe with that product as ingredient
    recipe_cat_id = conn.execute(
        text("SELECT id FROM recipe_categories LIMIT 1")
    ).scalar()
    conn.execute(
        text("INSERT INTO recipes (id, name, category_id, servings, user_id) "
             "VALUES (9000, 'Каскад-рецепт', :rcat, 1, 1)"),
        {"rcat": recipe_cat_id},
    )
    conn.execute(
        text("INSERT INTO recipe_ingredients (recipe_id, product_id, amount, unit) "
             "VALUES (9000, 9000, 100, 'g')")
    )
    # Create a menu slot referencing the product
    conn.execute(
        text("INSERT INTO menus (id, name, user_id) VALUES (9000, 'Тест-меню', 1)")
    )
    conn.execute(
        text("INSERT INTO menu_slots (menu_id, day, meal_type, product_id, slot_position) "
             "VALUES (9000, 1, 'breakfast', 9000, 0)")
    )
    conn.commit()

    repo.hard_delete(cat_id)

    # Product gone
    assert conn.execute(
        text("SELECT COUNT(*) FROM products WHERE id = 9000")
    ).scalar() == 0
    # Recipe ingredient gone
    assert conn.execute(
        text("SELECT COUNT(*) FROM recipe_ingredients WHERE product_id = 9000")
    ).scalar() == 0
    # Menu slot gone
    assert conn.execute(
        text("SELECT COUNT(*) FROM menu_slots WHERE product_id = 9000")
    ).scalar() == 0
    # Recipe itself still exists
    assert conn.execute(
        text("SELECT COUNT(*) FROM recipes WHERE id = 9000")
    ).scalar() == 1


def test_product_category_is_used_false(conn) -> None:
    repo = SqlAlchemyProductCategoryRepository(conn)
    new_id = repo.save("Пустая")
    assert repo.is_used(new_id) is False


def test_product_category_is_used_true(conn) -> None:
    repo = SqlAlchemyProductCategoryRepository(conn)
    new_id = repo.save("С продуктами")
    conn.execute(
        text("INSERT INTO products (name, brand, supplier, category_id, recipe_unit, purchase_unit, user_id) "
             "VALUES ('Тест', '', '', :cat_id, 'g', 'kg', 1)"),
        {"cat_id": new_id},
    )
    conn.commit()
    assert repo.is_used(new_id) is True


def test_recipe_category_find_all_includes_inactive(conn) -> None:
    conn.execute(text(
        "INSERT INTO recipe_categories (name, active) VALUES ('Старые', 0)"
    ))
    conn.commit()

    repo = SqlAlchemyRecipeCategoryRepository(conn)
    categories = repo.find_all()
    names = [name for _, name, _ in categories]
    assert "Старые" in names

    archived = [(cid, n, a) for cid, n, a in categories if n == "Старые"]
    assert archived[0][2] is False


def test_recipe_category_save_creates_new(conn) -> None:
    repo = SqlAlchemyRecipeCategoryRepository(conn)
    new_id = repo.save("Выпечка")
    assert isinstance(new_id, int)
    names = [name for _, name in repo.find_active()]
    assert "Выпечка" in names


def test_recipe_category_save_updates_existing(conn) -> None:
    repo = SqlAlchemyRecipeCategoryRepository(conn)
    new_id = repo.save("Тестовая")
    repo.save("Тестовая (изм.)", new_id)
    names = [name for _, name in repo.find_active()]
    assert "Тестовая (изм.)" in names
    assert "Тестовая" not in names


def test_recipe_category_delete_makes_inactive(conn) -> None:
    repo = SqlAlchemyRecipeCategoryRepository(conn)
    new_id = repo.save("Удаляемая")
    repo.delete(new_id)
    active_names = [name for _, name in repo.find_active()]
    assert "Удаляемая" not in active_names

    all_names = [name for _, name, _ in repo.find_all()]
    assert "Удаляемая" in all_names


def test_recipe_category_hard_delete_removes_row(conn) -> None:
    repo = SqlAlchemyRecipeCategoryRepository(conn)
    new_id = repo.save("Удаляемая навсегда")
    repo.hard_delete(new_id)
    all_names = [name for _, name, _ in repo.find_all()]
    assert "Удаляемая навсегда" not in all_names


def test_recipe_category_hard_delete_removes_linked_recipes(conn) -> None:
    repo = SqlAlchemyRecipeCategoryRepository(conn)
    new_id = repo.save("С рецептами")
    conn.execute(
        text("INSERT INTO recipes (name, category_id, servings, user_id) VALUES ('Тест-рецепт', :cat_id, 1, 1)"),
        {"cat_id": new_id},
    )
    conn.commit()
    repo.hard_delete(new_id)
    all_names = [name for _, name, _ in repo.find_all()]
    assert "С рецептами" not in all_names
    count = conn.execute(
        text("SELECT COUNT(*) FROM recipes WHERE category_id = :cat_id"),
        {"cat_id": new_id},
    ).scalar()
    assert count == 0


def test_recipe_category_hard_delete_cascades_to_menu_slots(conn) -> None:
    """Hard-deleting a recipe category must also remove recipe_ingredients,
    cooking_steps, and menu_slots that reference the deleted recipes."""
    repo = SqlAlchemyRecipeCategoryRepository(conn)
    cat_id = repo.save("Каскад-рец")

    # Create a recipe in this category with ingredient and step
    prod_cat_id = conn.execute(
        text("SELECT id FROM product_categories LIMIT 1")
    ).scalar()
    conn.execute(
        text("INSERT INTO products (id, name, brand, supplier, category_id, "
             "recipe_unit, purchase_unit, user_id) "
             "VALUES (9001, 'Каскад-прод', '', '', :pcat, 'g', 'kg', 1)"),
        {"pcat": prod_cat_id},
    )
    conn.execute(
        text("INSERT INTO recipes (id, name, category_id, servings, user_id) "
             "VALUES (9001, 'Каскад-рецепт', :cat_id, 1, 1)"),
        {"cat_id": cat_id},
    )
    conn.execute(
        text("INSERT INTO recipe_ingredients (recipe_id, product_id, amount, unit) "
             "VALUES (9001, 9001, 50, 'g')")
    )
    conn.execute(
        text("INSERT INTO cooking_steps (recipe_id, step_order, description) "
             "VALUES (9001, 1, 'Шаг 1')")
    )
    # Menu slot referencing the recipe
    conn.execute(
        text("INSERT INTO menus (id, name, user_id) VALUES (9001, 'Тест-меню', 1)")
    )
    conn.execute(
        text("INSERT INTO menu_slots (menu_id, day, meal_type, recipe_id, slot_position) "
             "VALUES (9001, 1, 'lunch', 9001, 0)")
    )
    conn.commit()

    repo.hard_delete(cat_id)

    # Recipe gone
    assert conn.execute(
        text("SELECT COUNT(*) FROM recipes WHERE id = 9001")
    ).scalar() == 0
    # Ingredients gone
    assert conn.execute(
        text("SELECT COUNT(*) FROM recipe_ingredients WHERE recipe_id = 9001")
    ).scalar() == 0
    # Steps gone
    assert conn.execute(
        text("SELECT COUNT(*) FROM cooking_steps WHERE recipe_id = 9001")
    ).scalar() == 0
    # Menu slot gone
    assert conn.execute(
        text("SELECT COUNT(*) FROM menu_slots WHERE recipe_id = 9001")
    ).scalar() == 0
    # Product still exists
    assert conn.execute(
        text("SELECT COUNT(*) FROM products WHERE id = 9001")
    ).scalar() == 1


def test_recipe_category_is_used_false(conn) -> None:
    repo = SqlAlchemyRecipeCategoryRepository(conn)
    new_id = repo.save("Пустая")
    assert repo.is_used(new_id) is False


def test_recipe_category_is_used_true(conn) -> None:
    repo = SqlAlchemyRecipeCategoryRepository(conn)
    new_id = repo.save("С рецептами")
    conn.execute(
        text("INSERT INTO recipes (name, category_id, servings, user_id) VALUES ('Тест', :cat_id, 1, 1)"),
        {"cat_id": new_id},
    )
    conn.commit()
    assert repo.is_used(new_id) is True


def test_product_category_activate_restores_hidden(conn) -> None:
    repo = SqlAlchemyProductCategoryRepository(conn)
    new_id = repo.save("Скрытая")
    repo.delete(new_id)
    assert "Скрытая" not in [name for _, name in repo.find_active()]

    repo.activate(new_id)
    active_names = [name for _, name in repo.find_active()]
    assert "Скрытая" in active_names


def test_recipe_category_activate_restores_hidden(conn) -> None:
    repo = SqlAlchemyRecipeCategoryRepository(conn)
    new_id = repo.save("Скрытая")
    repo.delete(new_id)
    assert "Скрытая" not in [name for _, name in repo.find_active()]

    repo.activate(new_id)
    active_names = [name for _, name in repo.find_active()]
    assert "Скрытая" in active_names


def test_product_category_save_reactivates_on_edit(conn) -> None:
    """Editing an inactive category should reactivate it."""
    repo = SqlAlchemyProductCategoryRepository(conn)
    new_id = repo.save("Скрытая")
    repo.delete(new_id)
    assert "Скрытая" not in [name for _, name in repo.find_active()]

    repo.save("Скрытая (восст.)", new_id)
    active_names = [name for _, name in repo.find_active()]
    assert "Скрытая (восст.)" in active_names


def test_recipe_category_save_reactivates_on_edit(conn) -> None:
    """Editing an inactive category should reactivate it."""
    repo = SqlAlchemyRecipeCategoryRepository(conn)
    new_id = repo.save("Скрытая")
    repo.delete(new_id)
    assert "Скрытая" not in [name for _, name in repo.find_active()]

    repo.save("Скрытая (восст.)", new_id)
    active_names = [name for _, name in repo.find_active()]
    assert "Скрытая (восст.)" in active_names
