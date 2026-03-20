# Планировщик меню — Техническое обзор

## Резюме проекта

**Планировщик меню** (Menutor) — это веб-приложение для планирования семейных приемов пищи, которое помогает семьям планировать еженедельные меню, управлять рецептами и продуктами, автоматически генерировать списки покупок с отслеживанием затрат и учитывать пищевые предпочтения. Проект — это полноценное приложение, находящееся в активной разработке.

**Статус:** MVP с завершенной веб-миграцией (490+ unit-тестов проходят)

## Технический стек

| Слой | Технология | Версия | Назначение |
|-------|-----------|---------|---------|
| **Бэкенд-фреймворк** | FastAPI | 0.100+ | HTTP API слой, маршрутизация запросов, внедрение зависимостей |
| **Python** | Python | 3.14 | Основное время выполнения через venv в `.venv3-14/` |
| **База данных** | PostgreSQL (prod) / SQLite (dev) | 15+ / 3.x | Постоянное хранение данных |
| **ORM** | SQLAlchemy | 2.0+ | Абстракция БД, маппинг моделей |
| **Миграции** | Alembic | 1.12+ | Версионирование схемы БД |
| **Хеширование пароля** | bcrypt | 4.0+ | Безопасное хранение пароля |
| **JWT** | PyJWT | 2.8+ | Генерация и валидация токенов сессий |
| **HTTP-сервер** | uvicorn | 0.23+ | ASGI-сервер для FastAPI |
| **Фронтенд-фреймворк** | Vue 3 | 3.3+ | Реактивный UI, компонент-ориентированный |
| **Язык фронтенда** | TypeScript | 5.0+ | Типобезопасный JavaScript для фронтенда |
| **Управление состоянием** | Pinia | 2.1+ | Централизованное хранилище (преемник Vuex) |
| **Маршрутизация** | Vue Router | 4.2+ | Клиентская SPA-маршрутизация |
| **HTTP-клиент** | axios | 1.4+ | Вызовы фронтенд → бэкенд API |
| **CSS-фреймворк** | Tailwind CSS | 4.0+ | Утилитарный стиль |
| **Node.js** | Node.js | 24.x via nvm | JavaScript среда, npm пакетный менеджер |
| **Тестирование (Бэкенд)** | pytest | 7.4+ | Unit и интеграционный тестовый фреймворк |
| **Тестирование (Фронтенд)** | Vitest | 1.0+ | Vue компонент и TS unit-тесты |
| **Качество кода** | mypy, isort, pre-commit | Latest | Проверка типов, сортировка импортов, git-hooks |

## Быстрый старт

### Настройка бэкенда

```bash
# Создать и активировать виртуальную среду
python3.14 -m venv .venv3-14
source .venv3-14/bin/activate

# Установить зависимости
pip install -r requirements.txt

# Запустить миграции БД
alembic upgrade head

# Запустить API-сервер
uvicorn backend.api.main:app --reload
```

API работает на `http://localhost:8000/docs` (Swagger UI).

### Настройка фронтенда

```bash
# Убедиться, что установлен Node.js 24 (через nvm)
nvm use 24

# Установить зависимости
cd frontend
npm install

# Запустить сервер разработки
npm run dev
```

Фронтенд работает на `http://localhost:5173`.

### Запустить тесты

```bash
# Бэкенд unit и интеграционные тесты
pytest tests/ -v

# Фронтенд компонент-тесты
cd frontend && npm run test

# Pre-commit проверки (mypy, isort, pytest)
pre-commit run --all-files
```

## Структура проекта

```
menu-planner/
├── backend/                            # Python бэкенд (FastAPI + Чистая архитектура)
│   ├── api/                            # HTTP слой: маршрутизаторы, схемы, аутентификация
│   │   ├── main.py                     # FastAPI приложение, lifespan, обработчики исключений
│   │   ├── auth.py                     # JWT извлечение (get_current_user зависимость)
│   │   ├── deps.py                     # FastAPI внедрение зависимостей (get_container)
│   │   ├── converters.py               # Доменная сущность → Pydantic схема преобразование
│   │   ├── routers/                    # 8 API маршрутизаторов (auth, recipes, products, menus, family, categories, shopping_list, import_export, system)
│   │   └── schemas/                    # Pydantic модели запроса/ответа
│   ├── domain/                         # Ядро бизнес-логики (ноль зависимостей фреймворка)
│   │   ├── entities/                   # Recipe, Product, Menu, ShoppingList, User, FamilyMember, RefreshToken
│   │   ├── value_objects/              # Quantity, Money, RecipeIngredient, CookingStep, Category
│   │   ├── services/                   # Доменные сервисы: ShoppingListBuilder, PortionCalculator, UnitConverter
│   │   ├── ports/                      # Абстрактные интерфейсы (репозитории, сервисы)
│   │   └── exceptions.py               # Пользовательские доменные исключения
│   ├── application/                    # Use case слой оркестрации
│   │   └── use_cases/                  # ~20 классов use case (1 класс = 1 операция)
│   ├── infrastructure/                 # Реализация доменных портов
│   │   ├── repositories/               # ORM модели SQLAlchemy и реализации репозиториев
│   │   ├── auth/                       # BcryptPasswordHasher, JwtTokenService
│   │   ├── database/                   # SQLAlchemy engine, миграции (Alembic)
│   │   ├── export/                     # CSV/JSON экспортеры (паттерн Strategy)
│   │   └── import_/                    # CSV/JSON импортеры
│   ├── composition/                    # Настройка контейнера внедрения зависимостей
│   │   ├── container.py                # ApplicationContainer орхестратор
│   │   ├── _auth.py, _recipes.py, etc. # Специфичная для модуля подключение
│   │   └── _infrastructure.py          # Инициализация БД и сервиса аутентификации
│   └── main.py                         # Точка входа для desktop/CLI (если используется)
│
├── frontend/                           # Vue 3 + TypeScript SPA
│   ├── src/
│   │   ├── main.ts                     # Инициализация Vue приложения
│   │   ├── App.vue                     # Root layout компонент (AppLayout + router-view)
│   │   ├── api/                        # HTTP клиент слой
│   │   │   ├── client.ts               # axios экземпляр с перехватчиками (JWT, auto-refresh)
│   │   │   ├── auth.ts                 # Вызовы Auth API (register, login, refresh)
│   │   │   └── types.ts                # TypeScript интерфейсы совпадающие с Pydantic схемами
│   │   ├── stores/                     # Pinia хранилища (реактивное состояние)
│   │   │   ├── auth.ts                 # Пользователь, токены доступа/обновления
│   │   │   ├── recipes.ts              # Список рецептов, CRUD операции
│   │   │   ├── products.ts             # Список продуктов, CRUD операции
│   │   │   ├── menus.ts                # Состояние еженедельного меню, управление слотом
│   │   │   ├── family.ts               # Члены семьи, пищевые ограничения
│   │   │   ├── categories.ts           # Категории продукта/рецепта
│   │   │   ├── shoppingList.ts         # Состояние списка покупок, отслеживание затрат
│   │   │   ├── toast.ts                # Очередь push-уведомлений
│   │   │   └── crud-factory.ts         # Генератор универсального CRUD хранилища
│   │   ├── router/                     # Конфигурация Vue Router
│   │   │   └── index.ts                # 6 основных маршрутов + вложенные дочерние /settings
│   │   ├── views/                      # Компоненты уровня страницы
│   │   │   ├── MenuPlannerView.vue     # Планировщик на 7 дней × 3 приема пищи сетка
│   │   │   ├── ShoppingListView.vue    # Агрегированный список покупок с отслеживанием затрат
│   │   │   ├── RecipeListView.vue      # CRUD таблица рецептов + форма
│   │   │   ├── ProductListView.vue     # CRUD таблица продуктов + форма
│   │   │   ├── SettingsView.vue        # Контейнер настроек (семья, категории, о программе)
│   │   │   └── AuthView.vue            # Страница входа/регистрации
│   │   ├── components/                 # Переиспользуемые компоненты
│   │   │   ├── layout/                 # AppSidebar, MobileBottomNav
│   │   │   ├── planner/                # PlannerGrid, GridCell, SourcePanel, SavedMenuList
│   │   │   ├── shopping/               # ShoppingTable, ShoppingSummary, AddProductForm
│   │   │   ├── recipes/                # RecipeTable, RecipeForm
│   │   │   ├── products/               # ProductTable, ProductForm
│   │   │   ├── settings/               # FamilyPanel, CategoryPanel, AboutPanel
│   │   │   └── ui/                     # Переиспользуемые примитивы (ConfirmDialog, InputDialog, ToastNotification, etc.)
│   │   ├── composables/                # Переиспользуемые функции компоновки
│   │   │   ├── useSelection.ts         # Логика многострочного выбора
│   │   │   ├── useDropdown.ts          # Состояние открытия/закрытия выпадающего списка
│   │   │   ├── useCategoryFilter.ts    # Логика фильтрации категорий
│   │   │   ├── useContextMenu.ts       # Контекстное меню правого клика
│   │   │   └── useFileDownload.ts      # Утилита загрузки blob/CSV экспорта
│   │   └── utils/                      # Функции утилиты
│   │       └── units.ts                # Преобразование единиц, форматирование меток
│   ├── public/                         # Статические активы
│   └── vite.config.ts                  # Плагин Tailwind v4, прокси API к :8000
│
├── tests/                              # Полный набор тестов
│   ├── unit/
│   │   ├── domain/                     # Тесты логики доменного слоя (Quantity, Recipe, etc.)
│   │   ├── application/                # Тесты use case
│   │   └── api/                        # Тесты эндпоинта маршрутизатора
│   └── integration/
│       └── repositories/               # ORM репозиторий тесты против :memory: SQLite
│
├── alembic/                            # Миграции БД (Alembic)
│   ├── env.py                          # Настройка среды миграции
│   └── versions/                       # Скрипты миграции с временными метками
│
├── .config/
│   ├── .env                            # Переменные окружения (git-игнорируется)
│   └── git-hooks/
│       └── pre-commit                  # Запускает pytest, isort, mypy перед коммитом
│
├── docs/                               # Пользовательская и техническая документация
│   ├── technical/                      # Этот каталог (архитектура, API, руководства реализации)
│   └── ...                             # Пользовательские руководства, спецификации (Russian)
│
├── requirements.txt                    # Зависимости Python (бэкенд + тесты)
├── frontend/package.json               # Зависимости Node (фронтенд)
├── pytest.ini                          # Конфигурация pytest
├── pyproject.toml                      # Конфигурация Python проекта (mypy, isort)
└── VERSION                             # Строка версии API
```

## Настройка окружения

### 1. Виртуальная среда Python

```bash
python3.14 -m venv .venv3-14
source .venv3-14/bin/activate  # macOS/Linux
# или
.venv3-14\Scripts\activate     # Windows
```

### 2. Переменные окружения

Создать `.config/.env`:

```env
DATABASE_URL=sqlite:///./test.db     # Dev: SQLite; Prod: postgresql://user:pass@host/db
JWT_SECRET_KEY=your-secret-key-here  # Генерировать с: openssl rand -hex 32
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30
```

### 3. Инициализация БД

```bash
# Создать/обновить схему
alembic upgrade head

# Если миграции не запускаются автоматически
python -c "from backend.infrastructure.database.seed_defaults import seed_defaults; seed_defaults()"
```

## Запуск приложения

### Разработка (FastAPI + Vue)

**Терминал 1 — Бэкенд:**

```bash
source .venv3-14/bin/activate
uvicorn backend.api.main:app --reload
# Документация Swagger API: http://localhost:8000/docs
# OpenAPI JSON: http://localhost:8000/openapi.json
```

**Терминал 2 — Фронтенд:**

```bash
cd frontend
npm run dev
# Фронтенд: http://localhost:5173
```

Прокси фронтенда в `vite.config.ts` перенаправляет вызовы API с `http://localhost:5173/api/*` на `http://localhost:8000/api/*`.

### Управление БД

```bash
# Создать миграцию (автоопределение изменений)
alembic revision --autogenerate -m "Опишите изменения"

# Применить все ожидающие миграции
alembic upgrade head

# Откатить одну миграцию
alembic downgrade -1

# Показать историю миграции
alembic history
```

## Ключевые решения в проектировании

### 1. Чистая архитектура (4 слоя + API адаптер)

- **Доменный слой:** Бизнес-логика, ноль зависимостей от фреймворков
- **Приложение:** Use cases, оркестрация, DTO
- **Инфраструктура:** Персистентность, аутентификация, file I/O
- **API:** FastAPI маршрутизаторы, Pydantic схемы, конвертеры
- **Фронтенд:** Vue 3 SPA с хранилищами Pinia

**Почему:** Максимальная тестируемость, независимость от фреймворка, четкое разделение ответственности.

### 2. Типизированные ID через `NewType`

```python
RecipeId = NewType("RecipeId", int)
ProductId = NewType("ProductId", int)
```

Предотвращает случайные ошибки смешивания ID (например, передача `ProductId` методу, ожидающему `RecipeId`). Применяется mypy во время компиляции.

### 3. SQLAlchemy + Alembic

- **SQLAlchemy:** Слой ORM между доменом и БД
- **Alembic:** Версионная миграция
- **Почему:** Простая поддержка нескольких БД (SQLite ↔ PostgreSQL), безопасная эволюция схемы, целостность данных

### 4. Pinia для управления состоянием фронтенда

- Централизованное, реактивное управление состоянием
- Меньше шаблонного кода, чем Vuex
- Плавная работа с Vue 3 Composition API

### 5. Tailwind CSS v4

- Утилитарный, адаптивный дизайн
- Ноль управления CSS файлами
- Встроен в Vite конвейер сборки

## Docker установка (опционально)

Для контейнеризованного развертывания:

```yaml
# docker-compose.yml структура
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: menutor
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass

  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://user:pass@db:5432/menutor
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
    depends_on:
      - db

  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    environment:
      VITE_API_BASE: http://api:8000
```

## Эндпоинты здоровья и мониторинга

- `GET /api/system/health` — Проверка здоровья (аутентификация не требуется)
- `GET /api/system/version` — Версия API
- `GET /docs` — Swagger UI со всеми эндпоинтами
- `GET /openapi.json` — OpenAPI/Swagger спецификация

## Частые задачи разработки

| Задача | Команда |
|--------|---------|
| Запустить тесты | `pytest tests/ -v --cov=backend` |
| Запустить тесты, соответствующие шаблону | `pytest tests/ -k "test_recipe" -v` |
| Форматировать импорты | `isort backend/ tests/` |
| Проверка типов | `mypy backend/ tests/` |
| Pre-commit проверка | `pre-commit run --all-files` |
| Собрать фронтенд | `cd frontend && npm run build` |
| Обслуживать построенные активы фронтенда | `cd frontend && npm run preview` |

---

**Далее:** См. [architecture.md](02-architecture.md) для подробных описаний слоев и паттернов проектирования.
