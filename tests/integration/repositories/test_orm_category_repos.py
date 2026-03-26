from sqlalchemy import text

from backend.infrastructure.repositories.orm_product_category_repository import (
    OrmProductCategoryRepository,
)
from backend.infrastructure.repositories.orm_recipe_category_repository import (
    OrmRecipeCategoryRepository,
)


def test_product_category_repo_returns_active(conn) -> None:
    repo = OrmProductCategoryRepository(conn)
    categories = repo.find_active()
    names = [c.name for c in categories]
    assert "Сыпучие" in names
    assert "Молочные" in names
    assert "Мясо" in names


def test_product_category_repo_returns_id_name_tuples(conn) -> None:
    repo = OrmProductCategoryRepository(conn)
    categories = repo.find_active()
    for cat in categories:
        assert isinstance(cat.id, int)
        assert isinstance(cat.name, str)


def test_product_category_repo_excludes_inactive(conn) -> None:
    conn.execute(text(
        "INSERT INTO product_categories (name, active) VALUES ('Архив', 0)"
    ))
    conn.commit()

    repo = OrmProductCategoryRepository(conn)
    categories = repo.find_active()
    names = [c.name for c in categories]

    assert "Архив" not in names


def test_product_category_repo_sorted(conn) -> None:
    repo = OrmProductCategoryRepository(conn)
    categories = repo.find_active()
    names = [c.name for c in categories]
    assert names == sorted(names)


def test_recipe_category_repo_returns_active(conn) -> None:
    repo = OrmRecipeCategoryRepository(conn)
    categories = repo.find_active()
    names = [c.name for c in categories]
    assert "Завтраки" in names
    assert "Основные" in names
    assert "Салаты" in names


def test_recipe_category_repo_returns_id_name_tuples(conn) -> None:
    repo = OrmRecipeCategoryRepository(conn)
    categories = repo.find_active()
    for cat in categories:
        assert isinstance(cat.id, int)
        assert isinstance(cat.name, str)


def test_recipe_category_repo_excludes_inactive(conn) -> None:
    conn.execute(text(
        "INSERT INTO recipe_categories (name, active) VALUES ('Старые', 0)"
    ))
    conn.commit()

    repo = OrmRecipeCategoryRepository(conn)
    categories = repo.find_active()
    names = [c.name for c in categories]

    assert "Старые" not in names


def test_recipe_category_repo_sorted(conn) -> None:
    repo = OrmRecipeCategoryRepository(conn)
    categories = repo.find_active()
    names = [c.name for c in categories]
    assert names == sorted(names)


# ── CRUD tests ─────────────────────────────────────────────────────────


def test_product_category_find_all_includes_inactive(conn) -> None:
    conn.execute(text(
        "INSERT INTO product_categories (name, active) VALUES ('Архив', 0)"
    ))
    conn.commit()

    repo = OrmProductCategoryRepository(conn)
    categories = repo.find_all()
    names = [c.name for c in categories]
    assert "Архив" in names

    archived = [c for c in categories if c.name == "Архив"]
    assert archived[0].active is False


def test_product_category_save_creates_new(conn) -> None:
    repo = OrmProductCategoryRepository(conn)
    new_id = repo.save("Замороженные")
    assert isinstance(new_id, int)
    names = [c.name for c in repo.find_active()]
    assert "Замороженные" in names


def test_product_category_save_updates_existing(conn) -> None:
    repo = OrmProductCategoryRepository(conn)
    new_id = repo.save("Тестовая")
    repo.save("Тестовая (изм.)", new_id)
    names = [c.name for c in repo.find_active()]
    assert "Тестовая (изм.)" in names
    assert "Тестовая" not in names


def test_product_category_delete_makes_inactive(conn) -> None:
    repo = OrmProductCategoryRepository(conn)
    new_id = repo.save("Удаляемая")
    repo.delete(new_id)
    active_names = [c.name for c in repo.find_active()]
    assert "Удаляемая" not in active_names

    all_names = [c.name for c in repo.find_all()]
    assert "Удаляемая" in all_names


def test_product_category_hard_delete_removes_row(conn) -> None:
    repo = OrmProductCategoryRepository(conn)
    new_id = repo.save("Удаляемая навсегда")
    repo.hard_delete(new_id)
    all_names = [c.name for c in repo.find_all()]
    assert "Удаляемая навсегда" not in all_names


def test_product_category_hard_delete_removes_linked_products(conn) -> None:
    repo = OrmProductCategoryRepository(conn)
    new_id = repo.save("С продуктами")
    conn.execute(
        text("INSERT INTO products (name, brand, supplier, category_id, recipe_unit, purchase_unit, user_id) "
             "VALUES ('Тест-продукт', '', '', :cat_id, 'g', 'kg', 1)"),
        {"cat_id": new_id},
    )
    conn.commit()
    repo.hard_delete(new_id)
    all_names = [c.name for c in repo.find_all()]
    assert "С продуктами" not in all_names
    count = conn.execute(
        text("SELECT COUNT(*) FROM products WHERE category_id = :cat_id"),
        {"cat_id": new_id},
    ).scalar()
    assert count == 0


def test_product_category_hard_delete_cascades_to_recipe_ingredients(conn) -> None:
    """Hard-deleting a product category must also remove recipe_ingredients
    and menu_slots that reference the deleted products."""
    repo = OrmProductCategoryRepository(conn)
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
    repo = OrmProductCategoryRepository(conn)
    new_id = repo.save("Пустая")
    assert repo.is_used(new_id) is False


def test_product_category_is_used_true(conn) -> None:
    repo = OrmProductCategoryRepository(conn)
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

    repo = OrmRecipeCategoryRepository(conn)
    categories = repo.find_all()
    names = [c.name for c in categories]
    assert "Старые" in names

    archived = [c for c in categories if c.name == "Старые"]
    assert archived[0].active is False


def test_recipe_category_save_creates_new(conn) -> None:
    repo = OrmRecipeCategoryRepository(conn)
    new_id = repo.save("Выпечка")
    assert isinstance(new_id, int)
    names = [c.name for c in repo.find_active()]
    assert "Выпечка" in names


def test_recipe_category_save_updates_existing(conn) -> None:
    repo = OrmRecipeCategoryRepository(conn)
    new_id = repo.save("Тестовая")
    repo.save("Тестовая (изм.)", new_id)
    names = [c.name for c in repo.find_active()]
    assert "Тестовая (изм.)" in names
    assert "Тестовая" not in names


def test_recipe_category_delete_makes_inactive(conn) -> None:
    repo = OrmRecipeCategoryRepository(conn)
    new_id = repo.save("Удаляемая")
    repo.delete(new_id)
    active_names = [c.name for c in repo.find_active()]
    assert "Удаляемая" not in active_names

    all_names = [c.name for c in repo.find_all()]
    assert "Удаляемая" in all_names


def test_recipe_category_hard_delete_removes_row(conn) -> None:
    repo = OrmRecipeCategoryRepository(conn)
    new_id = repo.save("Удаляемая навсегда")
    repo.hard_delete(new_id)
    all_names = [c.name for c in repo.find_all()]
    assert "Удаляемая навсегда" not in all_names


def test_recipe_category_hard_delete_removes_linked_recipes(conn) -> None:
    repo = OrmRecipeCategoryRepository(conn)
    new_id = repo.save("С рецептами")
    conn.execute(
        text("INSERT INTO recipes (name, category_id, servings, user_id) VALUES ('Тест-рецепт', :cat_id, 1, 1)"),
        {"cat_id": new_id},
    )
    conn.commit()
    repo.hard_delete(new_id)
    all_names = [c.name for c in repo.find_all()]
    assert "С рецептами" not in all_names
    count = conn.execute(
        text("SELECT COUNT(*) FROM recipes WHERE category_id = :cat_id"),
        {"cat_id": new_id},
    ).scalar()
    assert count == 0


def test_recipe_category_hard_delete_cascades_to_menu_slots(conn) -> None:
    """Hard-deleting a recipe category must also remove recipe_ingredients,
    cooking_steps, and menu_slots that reference the deleted recipes."""
    repo = OrmRecipeCategoryRepository(conn)
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
    repo = OrmRecipeCategoryRepository(conn)
    new_id = repo.save("Пустая")
    assert repo.is_used(new_id) is False


def test_recipe_category_is_used_true(conn) -> None:
    repo = OrmRecipeCategoryRepository(conn)
    new_id = repo.save("С рецептами")
    conn.execute(
        text("INSERT INTO recipes (name, category_id, servings, user_id) VALUES ('Тест', :cat_id, 1, 1)"),
        {"cat_id": new_id},
    )
    conn.commit()
    assert repo.is_used(new_id) is True


def test_product_category_activate_restores_hidden(conn) -> None:
    repo = OrmProductCategoryRepository(conn)
    new_id = repo.save("Скрытая")
    repo.delete(new_id)
    assert "Скрытая" not in [c.name for c in repo.find_active()]

    repo.activate(new_id)
    active_names = [c.name for c in repo.find_active()]
    assert "Скрытая" in active_names


def test_recipe_category_activate_restores_hidden(conn) -> None:
    repo = OrmRecipeCategoryRepository(conn)
    new_id = repo.save("Скрытая")
    repo.delete(new_id)
    assert "Скрытая" not in [c.name for c in repo.find_active()]

    repo.activate(new_id)
    active_names = [c.name for c in repo.find_active()]
    assert "Скрытая" in active_names


# ── move_and_delete tests ────────────────────────────────────────────


def test_product_category_move_and_delete(conn) -> None:
    """Products are moved to the target category, then the source category is deleted."""
    repo = OrmProductCategoryRepository(conn)
    from_id = repo.save("Переносимая")
    to_id = repo.save("Целевая")

    conn.execute(
        text(
            "INSERT INTO products (name, brand, supplier, category_id, recipe_unit, purchase_unit, user_id) "
            "VALUES ('Продукт1', '', '', :cat_id, 'g', 'kg', 1)"
        ),
        {"cat_id": from_id},
    )
    conn.execute(
        text(
            "INSERT INTO products (name, brand, supplier, category_id, recipe_unit, purchase_unit, user_id) "
            "VALUES ('Продукт2', '', '', :cat_id, 'g', 'kg', 1)"
        ),
        {"cat_id": from_id},
    )
    conn.commit()

    repo.move_and_delete(from_id, to_id)

    # Source category must be gone
    all_names = [c.name for c in repo.find_all()]
    assert "Переносимая" not in all_names

    # Both products are now in the target category
    count = conn.execute(
        text("SELECT COUNT(*) FROM products WHERE category_id = :cat_id"),
        {"cat_id": to_id},
    ).scalar()
    assert count == 2

    # No products remain in the (now deleted) source category
    count_old = conn.execute(
        text("SELECT COUNT(*) FROM products WHERE category_id = :cat_id"),
        {"cat_id": from_id},
    ).scalar()
    assert count_old == 0


def test_product_category_move_and_delete_rollback_on_invalid_target(conn) -> None:
    """If the target category does not exist, rollback and source category survives."""
    import pytest

    from backend.domain.exceptions import AppError

    repo = OrmProductCategoryRepository(conn)
    from_id = repo.save("Источник")

    non_existent_to_id = 999999

    with pytest.raises(AppError):
        repo.move_and_delete(from_id, non_existent_to_id)

    # Source category must still exist
    all_names = [c.name for c in repo.find_all()]
    assert "Источник" in all_names


def test_recipe_category_move_and_delete(conn) -> None:
    """Recipes are moved to the target category, then the source category is deleted."""
    repo = OrmRecipeCategoryRepository(conn)
    from_id = repo.save("Источник рецептов")
    to_id = repo.save("Цель рецептов")

    conn.execute(
        text(
            "INSERT INTO recipes (name, category_id, servings, user_id) "
            "VALUES ('Рецепт1', :cat_id, 1, 1)"
        ),
        {"cat_id": from_id},
    )
    conn.execute(
        text(
            "INSERT INTO recipes (name, category_id, servings, user_id) "
            "VALUES ('Рецепт2', :cat_id, 1, 1)"
        ),
        {"cat_id": from_id},
    )
    conn.commit()

    repo.move_and_delete(from_id, to_id)

    # Source category must be gone
    all_names = [c.name for c in repo.find_all()]
    assert "Источник рецептов" not in all_names

    # Both recipes are now in the target category
    count = conn.execute(
        text("SELECT COUNT(*) FROM recipes WHERE category_id = :cat_id"),
        {"cat_id": to_id},
    ).scalar()
    assert count == 2

    # No recipes remain in the (now deleted) source category
    count_old = conn.execute(
        text("SELECT COUNT(*) FROM recipes WHERE category_id = :cat_id"),
        {"cat_id": from_id},
    ).scalar()
    assert count_old == 0


def test_recipe_category_move_and_delete_rollback_on_invalid_target(conn) -> None:
    """If the target category does not exist, rollback and source category survives."""
    import pytest

    from backend.domain.exceptions import AppError

    repo = OrmRecipeCategoryRepository(conn)
    from_id = repo.save("Источник рец.")

    non_existent_to_id = 999999

    with pytest.raises(AppError):
        repo.move_and_delete(from_id, non_existent_to_id)

    # Source category must still exist
    all_names = [c.name for c in repo.find_all()]
    assert "Источник рец." in all_names


def test_product_category_save_reactivates_on_edit(conn) -> None:
    """Editing an inactive category should reactivate it."""
    repo = OrmProductCategoryRepository(conn)
    new_id = repo.save("Скрытая")
    repo.delete(new_id)
    assert "Скрытая" not in [c.name for c in repo.find_active()]

    repo.save("Скрытая (восст.)", new_id)
    active_names = [c.name for c in repo.find_active()]
    assert "Скрытая (восст.)" in active_names


def test_recipe_category_save_reactivates_on_edit(conn) -> None:
    """Editing an inactive category should reactivate it."""
    repo = OrmRecipeCategoryRepository(conn)
    new_id = repo.save("Скрытая")
    repo.delete(new_id)
    assert "Скрытая" not in [c.name for c in repo.find_active()]

    repo.save("Скрытая (восст.)", new_id)
    active_names = [c.name for c in repo.find_active()]
    assert "Скрытая (восст.)" in active_names
