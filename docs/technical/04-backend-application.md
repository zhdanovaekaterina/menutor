# Слой приложения — Use Cases

**Расположение файла:** `backend/application/use_cases/`

Слой приложения оркестрирует логику доменного слоя. **Один класс = одна пользовательская операция.** Use cases развязаны от HTTP, БД и UI.

---

## Паттерн Use case

Каждый use case — это класс с методом `execute()`. Паттерн:

```python
class SomeUseCase:
    def __init__(self, repository: SomeRepository, other_service: OtherService):
        self.repository = repository
        self.other_service = other_service

    def execute(self, param1: str, param2: int, user_id: UserId) -> ResultType:
        # 1. Валидировать входные данные
        if not param1.strip():
            raise DomainError("param1 требуется")

        # 2. Получить доменные объекты
        entity = self.repository.get_by_id(entity_id, user_id)
        if not entity:
            raise EntityNotFoundError("Сущность не найдена")

        # 3. Применить бизнес-логику
        entity.some_property = param2
        modified = self.other_service.transform(entity)

        # 4. Персистировать
        result_id = self.repository.save(modified)

        # 5. Вернуть значение (обычно ID или полная сущность)
        return result_id
```

**Преимущества:**
- **Тестируемо:** внедрить mock репозитории
- **Переиспользуемо:** можно вызвать из API, CLI, событий
- **Изолировано:** каждая операция независима
- **Отлаживаемо:** ясный поток входа → выхода

---

## Каталог use cases

### Модуль аутентификации

**Файл:** `backend/application/use_cases/auth.py`

#### RegisterUser

Создает новую учетную запись пользователя.

```python
class RegisterUser:
    def __init__(
        self,
        user_repo: UserRepository,
        password_hasher: PasswordHasher,
    ):
        self.user_repo = user_repo
        self.password_hasher = password_hasher

    def execute(self, email: str, password: str, nickname: str) -> UserId:
        """
        Зарегистрировать нового пользователя.

        Raises:
            UserAlreadyExistsError: Email уже зарегистрирован
            DomainError: Неверный email или пароль
        """
        # Проверить уникальность
        existing = self.user_repo.get_by_email(email)
        if existing:
            raise UserAlreadyExistsError(f"Email {email} уже зарегистрирован")

        # Хешировать пароль
        password_hash = self.password_hasher.hash_password(password)

        # Создать и сохранить
        user = User(
            id=UserId(0),  # БД присвоит
            email=email,
            nickname=nickname,
            password_hash=password_hash,
            created_at=datetime.utcnow(),
        )
        return self.user_repo.save(user)
```

#### LoginUser

Валидирует учетные данные и возвращает токены.

```python
class LoginUser:
    def __init__(
        self,
        user_repo: UserRepository,
        password_hasher: PasswordHasher,
        token_service: TokenService,
        refresh_token_repo: RefreshTokenRepository,
    ):
        self.user_repo = user_repo
        self.password_hasher = password_hasher
        self.token_service = token_service
        self.refresh_token_repo = refresh_token_repo

    def execute(self, email: str, password: str) -> LoginResponse:
        """
        Аутентифицировать пользователя и вернуть JWT токены.

        Returns:
            LoginResponse с access_token, refresh_token, token_type
        """
        user = self.user_repo.get_by_email(email)
        if not user or not self.password_hasher.verify_password(password, user.password_hash):
            raise AuthenticationError("Неверный email или пароль")

        # Создать токены
        access_token = self.token_service.create_access_token(
            user.id, expires_in_minutes=30
        )
        refresh_token = self.token_service.create_refresh_token(
            user.id, expires_in_days=30
        )

        # Сохранить хеш refresh токена
        token_hash = hash_token(refresh_token)
        self.refresh_token_repo.save(RefreshToken(
            id=RefreshTokenId(0),
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.utcnow() + timedelta(days=30),
            created_at=datetime.utcnow(),
        ))

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )
```

#### RefreshAccessToken

Выдает новый токен доступа используя refresh токен.

```python
class RefreshAccessToken:
    def __init__(
        self,
        token_service: TokenService,
        refresh_token_repo: RefreshTokenRepository,
    ):
        self.token_service = token_service
        self.refresh_token_repo = refresh_token_repo

    def execute(self, refresh_token: str) -> str:
        """Валидировать refresh токен и вернуть новый токен доступа."""
        payload = self.token_service.validate_token(refresh_token)

        # Проверить что токен не отозван
        token_hash = hash_token(refresh_token)
        stored = self.refresh_token_repo.get_by_hash(token_hash)
        if not stored or stored.revoked or stored.expires_at < datetime.utcnow():
            raise AuthenticationError("Refresh токен неверный или истек")

        # Выдать новый токен доступа
        new_access_token = self.token_service.create_access_token(
            stored.user_id, expires_in_minutes=30
        )
        return new_access_token
```

#### GetCurrentUser

Извлекает и валидирует JWT полезную нагрузку токена.

```python
class GetCurrentUser:
    def __init__(self, user_repo: UserRepository, token_service: TokenService):
        self.user_repo = user_repo
        self.token_service = token_service

    def execute(self, token: str) -> User:
        """Валидировать токен и вернуть текущего пользователя."""
        payload = self.token_service.validate_token(token)
        user_id = UserId(payload.get("user_id"))

        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise AuthenticationError("Пользователь не найден")

        return user
```

### Управление рецептами

**Файл:** `backend/application/use_cases/manage_recipe.py`

#### ListRecipes

```python
class ListRecipes:
    def __init__(self, recipe_repo: RecipeRepository):
        self.recipe_repo = recipe_repo

    def execute(
        self, user_id: UserId, category_id: RecipeCategoryId | None = None
    ) -> list[Recipe]:
        """Вывести все рецепты пользователя, опционально отфильтровано по категориям."""
        if category_id:
            return self.recipe_repo.list_by_category(user_id, category_id)
        return self.recipe_repo.list_by_user(user_id)
```

#### CreateRecipe

```python
class CreateRecipe:
    def __init__(self, recipe_repo: RecipeRepository):
        self.recipe_repo = recipe_repo

    def execute(
        self,
        user_id: UserId,
        name: str,
        servings: int,
        category_id: RecipeCategoryId,
        ingredients: list[RecipeIngredient],
        steps: list[CookingStep],
        weight: int = 0,
        total_pieces: int | None = None,
        pieces_per_portion: int | None = None,
    ) -> RecipeId:
        """Создать новый рецепт."""
        if not name.strip():
            raise DomainError("Требуется имя рецепта")
        if servings < 1:
            raise DomainError("Порции должны быть >= 1")

        recipe = Recipe(
            id=RecipeId(0),
            name=name.strip(),
            servings=servings,
            category_id=category_id,
            ingredients=ingredients,
            steps=steps,
            weight=weight,
            user_id=user_id,
            total_pieces=total_pieces,
            pieces_per_portion=pieces_per_portion,
        )

        return self.recipe_repo.save(recipe)
```

#### DeleteRecipe

```python
class DeleteRecipe:
    def __init__(self, recipe_repo: RecipeRepository):
        self.recipe_repo = recipe_repo

    def execute(self, recipe_id: RecipeId, user_id: UserId) -> None:
        """Удалить рецепт."""
        recipe = self.recipe_repo.get_by_id(recipe_id, user_id)
        if not recipe:
            raise EntityNotFoundError(f"Рецепт {recipe_id} не найден")
        self.recipe_repo.delete(recipe_id, user_id)
```

### Планирование меню

**Файл:** `backend/application/use_cases/plan_menu.py`

#### CreateMenu

```python
class CreateMenu:
    def __init__(self, menu_repo: MenuRepository):
        self.menu_repo = menu_repo

    def execute(self, user_id: UserId, name: str) -> MenuId:
        """Создать новое меню."""
        if not name.strip():
            raise DomainError("Требуется имя меню")

        menu = Menu(
            id=MenuId(0),
            name=name.strip(),
            created_at=datetime.utcnow(),
            user_id=user_id,
            slots=[],
        )
        return self.menu_repo.save(menu)
```

#### AddMenuSlot

```python
class AddMenuSlot:
    def __init__(self, menu_repo: MenuRepository, recipe_repo: RecipeRepository):
        self.menu_repo = menu_repo
        self.recipe_repo = recipe_repo

    def execute(
        self,
        menu_id: MenuId,
        user_id: UserId,
        recipe_id: RecipeId | None,
        product_id: ProductId | None,
        servings: int | None,
        quantity: Quantity | None,
        meal_type: str,
        day_of_week: int,
    ) -> MenuSlotId:
        """Добавить рецепт или продукт в слот меню."""
        menu = self.menu_repo.get_by_id(menu_id, user_id)
        if not menu:
            raise EntityNotFoundError(f"Меню {menu_id} не найдено")

        if recipe_id:
            recipe = self.recipe_repo.get_by_id(recipe_id, user_id)
            if not recipe:
                raise EntityNotFoundError(f"Рецепт {recipe_id} не найден")

        slot = MenuSlot(
            id=MenuSlotId(0),
            menu_id=menu_id,
            recipe_id=recipe_id,
            product_id=product_id,
            servings=servings,
            quantity=quantity,
            meal_type=meal_type,
            day_of_week=day_of_week,
            position=len([s for s in menu.slots if s.day_of_week == day_of_week and s.meal_type == meal_type]),
        )
        return self.menu_repo.add_slot(menu_id, slot)
```

### Генерация списка покупок

**Файл:** `backend/application/use_cases/generate_shopping_list.py`

#### GenerateShoppingList

Самый важный use case. Вызывает доменный сервис для оркестрации построения списка покупок.

```python
class GenerateShoppingList:
    def __init__(
        self,
        menu_repo: MenuRepository,
        recipe_repo: RecipeRepository,
        product_repo: ProductRepository,
        family_member_repo: FamilyMemberRepository,
        shopping_list_builder: ShoppingListBuilder,
    ):
        self.menu_repo = menu_repo
        self.recipe_repo = recipe_repo
        self.product_repo = product_repo
        self.family_member_repo = family_member_repo
        self.shopping_list_builder = shopping_list_builder

    def execute(self, menu_id: MenuId, user_id: UserId) -> ShoppingList:
        """
        Генерировать список покупок из меню + семья.

        Процесс:
        1. Загрузить меню со слотами
        2. Загрузить все рецепты, на которые ссылаются слоты
        3. Загрузить все продукты
        4. Загрузить членов семьи
        5. Вызвать ShoppingListBuilder для агрегирования
        """
        menu = self.menu_repo.get_by_id(menu_id, user_id)
        if not menu:
            raise EntityNotFoundError(f"Меню {menu_id} не найдено")

        # Получить все нужные рецепты
        recipe_ids = {s.recipe_id for s in menu.slots if s.recipe_id}
        recipes = {}
        for rid in recipe_ids:
            recipe = self.recipe_repo.get_by_id(rid, user_id)
            if recipe:
                recipes[rid] = recipe

        # Получить все продукты
        products_list = self.product_repo.list_by_user(user_id)
        products = {p.id: p for p in products_list}

        # Получить членов семьи
        family = self.family_member_repo.list_by_user(user_id)

        # Построить список покупок
        return self.shopping_list_builder.build(menu, family, products, recipes)
```

### Вложенные рецепты (выравнивание)

**Файл:** `backend/application/use_cases/flatten_recipe_products.py`

Разворачивает sub-рецепты в конечные продукты.

```python
class FlattenRecipeProducts:
    """
    Преобразовать рецепт с sub-рецептами в итоговый список продуктов.

    Пример:
        Рецепт "Борщ" включает:
        - Свеклу (продукт) 500g
        - "Овощной бульон" (sub-recipe) 1 литр

        Выравнивание разворачивает "Овощной бульон" в его продукты:
        - Вода 1L
        - Морковь 200g
        - Сельдерей 100g

        Результат: Свекла + Вода + Морковь + Сельдерей
    """

    def __init__(self, recipe_repo: RecipeRepository):
        self.recipe_repo = recipe_repo

    def execute(
        self,
        recipe_id: RecipeId,
        user_id: UserId,
    ) -> list[FlattenedProduct]:
        """Рекурсивно разворачивать sub-рецепты, обнаруживать циклы."""
        visited: set[RecipeId] = set()
        flattened: list[FlattenedProduct] = []

        def flatten_recursive(rid: RecipeId, factor: float, depth: int = 0) -> None:
            if depth > MAX_NESTING_DEPTH:
                raise NestingDepthExceededError(f"Глубина вложения > {MAX_NESTING_DEPTH}")

            if rid in visited:
                raise CircularDependencyError(f"Циклическая зависимость обнаружена на {rid}")

            visited.add(rid)
            recipe = self.recipe_repo.get_by_id(rid, user_id)
            if not recipe:
                raise EntityNotFoundError(f"Рецепт {rid} не найден")

            for ing in recipe.ingredients:
                if ing.is_product():
                    scaled_qty = Quantity(ing.quantity.amount * factor, ing.quantity.unit)
                    flattened.append(FlattenedProduct(
                        product_id=ing.product_id,
                        quantity=scaled_qty,
                    ))
                else:
                    # Разворачивать sub-рецепт
                    flatten_recursive(ing.sub_recipe_id, ing.quantity.amount * factor, depth + 1)

            visited.discard(rid)

        flatten_recursive(recipe_id, 1.0)
        return flattened
```

---

## Обработка ошибок

1. **Валидировать входные данные** → выбросить `DomainError` (400)
2. **Сущность не найдена** → выбросить `EntityNotFoundError` (404)
3. **Конфликт пользователя** → выбросить `UserAlreadyExistsError` (409)
4. **Аутентификация не прошла** → выбросить `AuthenticationError` (401)
5. **Нарушение бизнес-правила** → выбросить специфичную доменную ошибку (422)

Все исключения перехватываются обработчиками исключений FastAPI в `backend/api/main.py` и преобразуются в JSON ответы.

---

## Тестирование use cases

**Паттерн:** Моки репозитории, вызвать `execute()`, утверждать результаты.

```python
# tests/unit/application/test_manage_recipe.py

def test_create_recipe():
    # Моки репозиторий
    repo = Mock(spec=RecipeRepository)
    repo.save.return_value = RecipeId(1)

    # Создать use case
    uc = CreateRecipe(repo)

    # Выполнить
    result = uc.execute(
        user_id=UserId(1),
        name="Блины",
        servings=4,
        category_id=RecipeCategoryId(1),
        ingredients=[...],
        steps=[...],
    )

    # Утверждать
    assert result == RecipeId(1)
    repo.save.assert_called_once()

def test_create_recipe_validation():
    repo = Mock(spec=RecipeRepository)
    uc = CreateRecipe(repo)

    # Должно выбросить DomainError на пустое имя
    with pytest.raises(DomainError):
        uc.execute(
            user_id=UserId(1),
            name="",  # Неверно
            servings=4,
            category_id=RecipeCategoryId(1),
            ingredients=[],
            steps=[],
        )
```

---

## Резюме

Слой приложения:
- **Оркестрирует** логику домена и репозитории
- **Валидирует** входные данные и применяет бизнес-правила
- **Обрабатывает** транзакции и персистентность
- **Тестируемо** через внедрение зависимостей
- **Переиспользуемо** из API, CLI или событий

Каждый use case представляет одну пользовательскую операцию, делая кодовую базу легко понятной и поддерживаемой.

---

**Далее:** См. [backend-infrastructure.md](05-backend-infrastructure.md) для деталей репозиториев и ORM.
