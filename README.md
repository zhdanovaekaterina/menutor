# Menutor

![Version](https://img.shields.io/badge/version-0.15.1-green.svg)
![License](https://img.shields.io/badge/license-GPL--3.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.12%2B-blue.svg)

Веб-приложение для планирования семейного меню, управления рецептами и продуктами и автоматического расчёта списка покупок.

## Возможности

- **Рецепты и продукты:** ингредиенты, шаги приготовления, категории, цены и закупочные единицы.
- **Планирование меню:** недельные меню, настраиваемые типы приёмов пищи, порции для всей семьи или отдельных её членов.
- **Составные рецепты:** вложенные рецепты, проверка циклических зависимостей и ограничение глубины вложенности.
- **Список покупок:** агрегация ингредиентов из меню, пересчёт единиц измерения, группировка по категориям, стоимость и отметки о покупке.
- **Пищевые предпочтения:** ограничения и аллергии членов семьи; проверка совместимости рецептов, в том числе с учётом вложенных блюд.
- **Расчёт стоимости рецепта:** стоимость порции, предварительный расчёт и детализация по ингредиентам.
- **Импорт и экспорт:** обмен данными и экспорт списков покупок; доступны форматы CSV, JSON, TXT и PDF в соответствующих сценариях.
- **Пользовательские аккаунты:** регистрация, вход, обновление и отзыв refresh-токенов, управление профилем.

## Технологии

| Область | Технологии |
| --- | --- |
| Backend | Python 3.12+, FastAPI, Pydantic |
| Данные | SQLAlchemy 2, PostgreSQL; SQLite для локальной разработки и тестов |
| Миграции | Alembic |
| Аутентификация | JWT (PyJWT), bcrypt |
| Экспорт PDF | ReportLab |
| Frontend | Vue 3, TypeScript, Pinia, Vue Router, Tailwind CSS 4 |
| Проверки | pytest, pytest-cov, mypy, isort, Black, Pylint; Vitest, vue-tsc |
| Контейнеры | Docker, Docker Compose |

## Архитектура

Backend разделён на API-адаптер, application use cases, доменную модель и инфраструктурные реализации. Зависимости инициализируются в composition root.

```text
backend/
├── api/             # FastAPI routers, Pydantic schemas, auth, converters
├── application/     # Use cases, DTO и прикладные порты
├── domain/          # Сущности, value objects, сервисы и порты
├── infrastructure/  # SQLAlchemy, репозитории, auth, импорт/экспорт
└── composition/     # Сборка зависимостей приложения
```

Доменная логика включает вычисление порций, конвертацию единиц и агрегацию покупок с расчётом стоимости. Данные основных сущностей ограничены пользователем; HTTP API документируется через OpenAPI.

## Локальный запуск

Нужны Python 3.12+ и Node.js 20.19+ или 22.12+.

### Backend

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn backend.api.main:app --reload
```

Если `.config/.env` отсутствует, приложение использует SQLite и `data/menutor.db`. Для PostgreSQL скопируйте `.config/.env.example` в `.config/.env` и укажите параметры своей базы данных и `JWT_SECRET_KEY`. Применение миграций:

```bash
alembic upgrade head
```

Документация API после запуска доступна по адресу <http://localhost:8000/docs>.

### Frontend

```bash
cd frontend
npm ci
npm run dev
```

Vite запускает frontend на <http://localhost:5173> и проксирует API-запросы к backend.

## Тесты и проверки

Backend unit-, API-, integration- и E2E-тесты:

```bash
pytest tests/ -v
```

Frontend-тесты и production-сборка:

```bash
cd frontend
npm ci
npm test
npm run build
```

Тесты backend находятся в `tests/unit/`, `tests/integration/` и `tests/e2e/`. Интеграционные тесты репозиториев используют SQLite in-memory.

## Развёртывание

В репозитории есть Docker Compose конфигурации для разработки и production. GitHub Actions workflow выполняет обновление контейнеров на self-hosted runner при push в `master`: [deploy.yml](.github/workflows/deploy.yml). Отдельный CI workflow для автоматического запуска тестов при pull request пока не настроен.

## Документация

- [Техническая документация](docs/technical/README.md)
- [Руководство пользователя](docs/user_guide.md)
- [История изменений](docs/changelog.md)

## Лицензия

Проект распространяется под лицензией GNU GPL v3.0. Подробности — в файле [LICENSE](LICENSE).

## Поддержка

Сообщить об ошибке или предложить улучшение можно в [GitHub Issues](https://github.com/zhdanovaekaterina/menutor/issues).