# Штучный режим рецептов (v0.7.0)

## Обзор

В версии 0.7.0 добавлен **штучный режим** для рецептов — возможность задать количество штук (`total_pieces`) и штук на порцию (`pieces_per_portion`). Это удобно для дискретных блюд (печенье, котлеты, пирожки), где количество естественно выражается в штуках, а не в порциях или граммах.

Количество порций при штучном режиме рассчитывается автоматически: `servings = floor(total_pieces / pieces_per_portion)`.

---

## Изменения в базе данных

Миграция `94b6b0751ebe_add_pieces_mode_fields.py` добавляет nullable-колонки:

| Таблица | Колонка | Тип | Описание |
|---|---|---|---|
| `recipes` | `total_pieces` | `INTEGER` | Общее количество штук рецепта |
| `recipes` | `pieces_per_portion` | `INTEGER` | Штук на одну порцию |
| `menu_slots` | `pieces_override` | `INTEGER` | Переопределение количества штук для конкретного слота |

Все три колонки nullable — их отсутствие (NULL) означает, что штучный режим не используется.

---

## Доменный слой

### `RecipeData` (application/use_cases/manage_recipe.py)

Добавлены два опциональных поля:

```python
@dataclass
class RecipeData:
    ...
    total_pieces: int | None = None
    pieces_per_portion: int | None = None
```

Передаются в `_build_recipe()` и сохраняются в сущности `Recipe`.

---

## Инфраструктурный слой

### ORM-модели (infrastructure/database/models.py)

`RecipeRow` получает колонки `total_pieces` и `pieces_per_portion`.
`MenuSlotRow` получает колонку `pieces_override`.

### Репозитории

- `SQLAlchemyRecipeRepository` — маппинг `total_pieces`, `pieces_per_portion` при чтении и записи рецептов.
- `SQLAlchemyMenuRepository` — маппинг `pieces_override` при чтении и записи слотов.

---

## API слой

### Схемы (api/schemas/recipe.py)

```python
class RecipeBase(BaseModel):
    ...
    total_pieces: int | None = None
    pieces_per_portion: int | None = None
```

### Схемы (api/schemas/menu.py)

```python
class MenuSlot(BaseModel):
    ...
    pieces_override: int | None = None
```

### Конвертеры (api/converters.py)

Конвертер доменного объекта в схему включает новые поля во всех 4 маршрутах (GET/POST/PUT для рецептов, GET для слотов меню).

---

## Экспорт и импорт

### Экспорт рецептов

- **CSV** (`recipe_csv_exporter.py`): добавлены колонки `total_pieces` и `pieces_per_portion`.
- **JSON** (`recipe_json_exporter.py`): добавлены поля `total_pieces` и `pieces_per_portion`.

### Экспорт меню

- **JSON** (`menu_json_exporter.py`): в объект слота добавлено поле `pieces_override`.

### Импорт (обратная совместимость)

Все три импортёра (`recipe_csv_importer.py`, `recipe_json_importer.py`, `menu_json_importer.py`) читают новые поля как опциональные с дефолтом `None`. Файлы, созданные до v0.7.0, импортируются без ошибок.

---

## Фронтенд

### Форма рецепта (RecipeForm.vue)

- Добавлен toggle-переключатель «Считать в штуках» (`isPiecesMode`).
- При включении — отображаются поля `totalPieces` и `piecesPerPortion`.
- `autoServings` — вычисляемое свойство: `floor(totalPieces / piecesPerPortion)`.
- При сохранении `servings` подставляется из `autoServings`, а `total_pieces`/`pieces_per_portion` передаются в `RecipeCreate`.
- Валидация: оба поля обязательны; `pieces_per_portion <= total_pieces`.

### Отображение в ячейке (ItemRow.vue, GridCell.vue)

- `ItemRow` принимает проп `piecesDetail` и рендерит «X п. · Y шт».
- `GridCell` вычисляет `piecesDetail` из данных рецепта и `pieces_override` слота.

### Диалог редактирования (SlotEditDialog.vue)

Новый компонент для редактирования `pieces_override` конкретного слота:
- Открывается при клике на ячейку с рецептом в штучном режиме.
- Показывает `portions` (readonly) и редактируемое поле штук.
- Эмитирует `confirm`, `cancel`, `delete`, `update:pieces`.
- При потере фокуса (`onBlur`) округляет значение до целого, минимум 1.

### MenuPlannerView.vue

Интегрирует `SlotEditDialog`: отслеживает состояние открытия диалога, передаёт текущие данные слота, обрабатывает подтверждение через обновление `pieces_override` в store.

---

## Тестирование

Добавлены тесты в `tests/integration/infrastructure/`:

- `test_recipe_exporters_pieces.py` — 103 строки, покрывает экспорт CSV/JSON с pieces-полями.
- `test_recipe_importers_pieces.py` — 152 строки, покрывает импорт с pieces-полями и без них.
- `test_menu_exporters_pieces.py` — 114 строк, покрывает экспорт/импорт `pieces_override` в JSON меню.
- `test_recipe_csv_exporter.py` — обновлён для новых колонок.

API-тесты в `tests/unit/api/` обновлены для новых полей схем.
