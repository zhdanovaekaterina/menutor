# Version 0.14.0 — Meal Type Management System

Technical documentation for version 0.14.0: a complete meal type management system allowing users to create, edit, and delete custom meal types (breakfast, lunch, dinner, snacks, etc.) as full domain entities. Meal types are no longer hardcoded strings but are now stored in the database with timestamps and user ownership.

## Overview

The meal type system enables users to customize their meal structure beyond the three built-in types (Breakfast, Lunch, Dinner). Each user has three system meal types created automatically on registration, plus the ability to create up to 10 custom meal types. Menu slots now reference meal types by ID instead of string names, providing type safety and better data integrity.

**Key features:**
- System meal types (Breakfast 08:00, Lunch 13:00, Dinner 18:00) auto-created per user
- Custom meal type creation with arbitrary names and times
- Limit of 10 custom meal types per user
- System types cannot be deleted (but can be edited)
- Usage checking before deletion with warning dialogs
- Automatic sorting by time, then by creation order
- Full CRUD operations via REST API
- Pinia store for frontend state management
- Migration of existing menu slots from string-based to ID-based references

## Domain Layer

### MealType Entity

**File:** `backend/domain/entities/meal_type.py`

```python
@dataclass
class MealType:
    id: MealTypeId                    # Unique identifier (type alias: NewType('MealTypeId', int))
    user_id: UserId                   # Owner of this meal type
    name: str                         # "Завтрак", "Полдник", etc. (1-50 chars)
    time: time                        # datetime.time object (e.g., time(8, 0))
    is_system: bool                   # True for built-in types (Breakfast, Lunch, Dinner)
    sort_order: int                   # Secondary sort key when times are equal

    MAX_CUSTOM_PER_USER: int = 10     # Constant: max 10 custom meal types per user
    MAX_NAME_LENGTH: int = 50         # Constant: max 50 characters for name
```

**Validations (implicit in domain logic):**
- Name length: 1 to 50 characters
- Names must be unique per user (enforced by repository and database constraint)
- System meal types have `is_system=True` and cannot be deleted
- Custom meal types have `is_system=False` and can be created up to the limit

### MealTypeRepository Port

**File:** `backend/domain/ports/meal_type_repository.py`

Abstract repository defining all operations on meal types:

```python
class MealTypeRepository(ABC):
    @abstractmethod
    def get_by_id(self, id: MealTypeId) -> MealType | None:
        """Fetch a single meal type by ID."""

    @abstractmethod
    def find_all(self, user_id: UserId) -> list[MealType]:
        """Fetch all meal types owned by a user (system + custom)."""

    @abstractmethod
    def find_by_name(self, user_id: UserId, name: str) -> MealType | None:
        """Case-insensitive search for a meal type by name."""

    @abstractmethod
    def count_custom(self, user_id: UserId) -> int:
        """Count user-created (non-system) meal types."""

    @abstractmethod
    def save(self, meal_type: MealType) -> MealType:
        """Create or update (INSERT or UPDATE)."""

    @abstractmethod
    def delete(self, ids: list[MealTypeId]) -> None:
        """Delete meal types by ID list."""

    @abstractmethod
    def get_usage(self, meal_type_id: MealTypeId) -> list[tuple[int, str]]:
        """Returns [(menu_id, menu_name), ...] for menus using this type."""
```

## Application Layer

### Meal Type Use Cases

**File:** `backend/application/use_cases/manage_meal_type.py`

#### ListMealTypes

```python
class ListMealTypes:
    def __init__(self, repo: MealTypeRepository) -> None: ...

    def execute(self, user_id: UserId) -> list[MealType]:
        """
        Fetch all meal types owned by the user and sort them:
        - By time (ascending)
        - By sort_order (ascending)
        - By ID (ascending)
        Returns: sorted list of meal types.
        """
```

#### CreateMealType

```python
@dataclass
class MealTypeData:
    name: str      # 1-50 characters
    time: time     # datetime.time object

class CreateMealType:
    def __init__(self, repo: MealTypeRepository) -> None: ...

    def execute(self, data: MealTypeData, user_id: UserId) -> MealType:
        """
        Create a new custom meal type for the user.

        Validations:
        - Name must be 1-50 characters, stripped of whitespace.
        - Name must be unique per user (raises DuplicateNameError).
        - User must not have reached the 10-custom-type limit (raises MealTypeLimitError).
        - sort_order is auto-assigned as max(existing sort_orders) + 1.

        Returns: saved meal type with auto-assigned ID.
        Raises: ValueError, DuplicateNameError, MealTypeLimitError.
        """
```

#### UpdateMealType

```python
class UpdateMealType:
    def __init__(self, repo: MealTypeRepository) -> None: ...

    def execute(
        self, meal_type_id: MealTypeId, data: MealTypeData, user_id: UserId
    ) -> MealType:
        """
        Update an existing meal type (name and/or time).

        Validations:
        - Meal type must exist and belong to the user (raises AccessDeniedError).
        - Name must be 1-50 characters, stripped.
        - Name must remain unique per user, allowing same name for same ID (raises DuplicateNameError).

        Returns: updated meal type.
        Raises: ValueError, AccessDeniedError, DuplicateNameError.
        """
```

#### DeleteMealType

```python
class DeleteMealType:
    def __init__(self, repo: MealTypeRepository) -> None: ...

    def execute(self, meal_type_id: MealTypeId, user_id: UserId) -> None:
        """
        Delete a meal type by ID.

        Validations:
        - Meal type must exist and belong to the user (raises AccessDeniedError).
        - Meal type must not be a system type (raises SystemMealTypeDeletionError: "Системные типы приемов пищи нельзя удалить").

        Note: Deletion is allowed even if the meal type is used in menus.
               Menu slots referencing this type will be deleted due to FK CASCADE.

        Returns: None.
        Raises: AccessDeniedError, SystemMealTypeDeletionError.
        """
```

#### CheckMealTypeUsage

```python
class CheckMealTypeUsage:
    def __init__(self, repo: MealTypeRepository) -> None: ...

    def execute(
        self, meal_type_id: MealTypeId, user_id: UserId
    ) -> list[tuple[int, str]]:
        """
        Check if a meal type is used in any menus.

        Returns: list of (menu_id, menu_name) tuples. Empty if not used.
        Raises: AccessDeniedError if type doesn't exist or doesn't belong to user.
        """
```

#### CreateSystemMealTypes

```python
SYSTEM_MEAL_TYPES = [
    ("Завтрак", time(8, 0), 0),     # Breakfast, 08:00, sort_order=0
    ("Обед", time(13, 0), 1),       # Lunch, 13:00, sort_order=1
    ("Ужин", time(18, 0), 2),       # Dinner, 18:00, sort_order=2
]

class CreateSystemMealTypes:
    def __init__(self, repo: MealTypeRepository) -> None: ...

    def execute(self, user_id: UserId) -> list[MealType]:
        """
        Create the 3 built-in meal types for a new user.

        Triggered automatically on user registration (in the user registration flow).
        All 3 types are marked with is_system=True.

        Returns: list of created meal types (system only).
        """
```

### Exception Classes

New exceptions in `backend/domain/exceptions.py`:

```python
class MealTypeLimitError(Exception):
    """Raised when attempting to create more than 10 custom meal types."""
    pass

class SystemMealTypeDeletionError(Exception):
    """Raised when attempting to delete a system meal type."""
    pass
```

## Infrastructure Layer

### ORM Model

**File:** `backend/infrastructure/database/models.py`

```python
class MealTypeRow(Base):
    __tablename__ = "meal_types"
    __table_args__ = (
        sa.UniqueConstraint("user_id", "name", name="uq_meal_types_user_name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str]                     # Unique per (user_id, name)
    time: Mapped[str]                     # Stored as "HH:MM" (5 chars)
    is_system: Mapped[bool] = mapped_column(default=False, server_default="0")
    sort_order: Mapped[int] = mapped_column(default=0, server_default="0")
```

### Database Schema

**Migration ID:** `a1b2c3d4e5e7` (dated 2026-04-03)

**Upgrade path:**
1. Create `meal_types` table with 3 system types per existing user
2. Create custom types from existing non-standard meal type strings in menu_slots
3. Add `meal_type_id` column to `menu_slots` (initially nullable)
4. Migrate all slot references from string name to ID (JOIN on user_id and name)
5. Add NOT NULL constraint and foreign key to `meal_type_id`
6. Drop the old `meal_type` text column

**Key SQL statements from migration:**

```sql
-- Create meal_types table
CREATE TABLE meal_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    time TEXT(5) NOT NULL,
    is_system BOOLEAN NOT NULL DEFAULT 0,
    sort_order INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE (user_id, name)
);

-- Migrate menu_slots: old column "meal_type" (TEXT) → new column "meal_type_id" (INT FK)
ALTER TABLE menu_slots ADD COLUMN meal_type_id INTEGER;
-- ... populate meal_type_id from JOIN ...
-- ... make NOT NULL and add FK constraint ...
ALTER TABLE menu_slots DROP COLUMN meal_type;
```

### Repository Implementation

**File:** `backend/infrastructure/repositories/sqlalchemy_meal_type_repository.py`

Standard CRUD repository translating between `MealTypeRow` (ORM) and `MealType` (domain entity):

**Key methods:**

```python
def find_all(self, user_id: UserId) -> list[MealType]:
    """Fetch all meal types for a user; no sorting (sorting done in use case)."""
    return [
        self._row_to_entity(row)
        for row in self.session.query(MealTypeRow).filter_by(user_id=user_id).all()
    ]

def find_by_name(self, user_id: UserId, name: str) -> MealType | None:
    """Case-insensitive search (LOWER in SQL where applicable)."""
    row = self.session.query(MealTypeRow).filter(
        MealTypeRow.user_id == user_id,
        func.lower(MealTypeRow.name) == func.lower(name)
    ).first()
    return self._row_to_entity(row) if row else None

def count_custom(self, user_id: UserId) -> int:
    """Count only is_system=False types."""
    return self.session.query(MealTypeRow).filter(
        MealTypeRow.user_id == user_id,
        MealTypeRow.is_system == False
    ).count()

def get_usage(self, meal_type_id: MealTypeId) -> list[tuple[int, str]]:
    """Find menus using this meal type."""
    result = self.session.query(MenuRow.id, MenuRow.name).join(
        MenuSlotRow, MenuRow.id == MenuSlotRow.menu_id
    ).filter(
        MenuSlotRow.meal_type_id == meal_type_id
    ).distinct().all()
    return [(m.id, m.name) for m in result]
```

## API Layer

### Router

**File:** `backend/api/routers/meal_types.py`

```python
router = APIRouter(prefix="/meal-types", tags=["meal-types"])

@router.get("", response_model=list[MealTypeResponse])
def list_meal_types(
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> list[MealTypeResponse]:
    """GET /meal-types — List all meal types for the current user."""

@router.post("", response_model=MealTypeResponse, status_code=status.HTTP_201_CREATED)
def create_meal_type(
    body: MealTypeCreate,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> MealTypeResponse:
    """POST /meal-types — Create a new meal type."""

@router.put("/{meal_type_id}", response_model=MealTypeResponse)
def update_meal_type(
    meal_type_id: int,
    body: MealTypeUpdate,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> MealTypeResponse:
    """PUT /meal-types/{id} — Update a meal type."""

@router.delete("/{meal_type_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meal_type(
    meal_type_id: int,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> None:
    """DELETE /meal-types/{id} — Delete a meal type."""

@router.get("/{meal_type_id}/usage", response_model=MealTypeUsageResponse)
def check_meal_type_usage(
    meal_type_id: int,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> MealTypeUsageResponse:
    """GET /meal-types/{id}/usage — Check if meal type is used in menus."""
```

### Request/Response Schemas

**File:** `backend/api/schemas/meal_type.py`

```python
class MealTypeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    time: str = Field(..., pattern=r"^([01]\d|2[0-3]):([0-5]\d)$")  # HH:MM format

class MealTypeUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    time: str = Field(..., pattern=r"^([01]\d|2[0-3]):([0-5]\d)$")

class MealTypeResponse(BaseModel):
    id: int
    name: str
    time: str                         # "08:00", "13:00", etc.
    is_system: bool
    sort_order: int

class MealTypeUsageMenu(BaseModel):
    id: int
    name: str

class MealTypeUsageResponse(BaseModel):
    meal_type_id: int
    menus: list[MealTypeUsageMenu]    # Empty if not used
    count: int                         # len(menus)
```

### Converters

**File:** `backend/api/converters.py`

```python
def meal_type_to_response(mt: MealType) -> MealTypeResponse:
    """Convert domain MealType to API response."""
    return MealTypeResponse(
        id=mt.id,
        name=mt.name,
        time=mt.time.strftime("%H:%M"),
        is_system=mt.is_system,
        sort_order=mt.sort_order,
    )

def meal_type_usage_to_response(
    meal_type_id: int, menus: list[tuple[int, str]]
) -> MealTypeUsageResponse:
    """Convert usage tuples to response."""
    menu_list = [MealTypeUsageMenu(id=m_id, name=m_name) for m_id, m_name in menus]
    return MealTypeUsageResponse(
        meal_type_id=meal_type_id,
        menus=menu_list,
        count=len(menu_list),
    )
```

## Frontend Layer

### Pinia Store

**File:** `frontend/src/stores/mealTypes.ts`

```typescript
export const useMealTypeStore = defineStore('mealTypes', () => {
  const items = ref<MealType[]>([])
  const loading = ref(false)

  // Computed: sorted meal types
  const sorted = computed(() =>
    [...items.value].sort((a, b) => {
      if (a.time !== b.time) return a.time.localeCompare(b.time)
      if (a.sort_order !== b.sort_order) return a.sort_order - b.sort_order
      return a.id - b.id
    }),
  )

  // Computed: count of user-created types
  const customCount = computed(() =>
    items.value.filter((t) => !t.is_system).length,
  )

  async function load(): Promise<void> {
    /* Fetch all meal types */
  }

  async function create(data: MealTypeCreate): Promise<MealType | null> {
    /* POST /meal-types, add to items, show toast */
  }

  async function update(id: number, data: MealTypeCreate): Promise<MealType | null> {
    /* PUT /meal-types/{id}, update items, show toast */
  }

  async function remove(id: number): Promise<boolean> {
    /* DELETE /meal-types/{id}, filter items, show toast */
  }

  async function checkUsage(id: number): Promise<MealTypeUsageResponse | null> {
    /* GET /meal-types/{id}/usage */
  }

  return {
    items,
    sorted,
    customCount,
    loading,
    load,
    create,
    update,
    remove,
    checkUsage,
  }
})
```

### Components

**MealTypePanel.vue** (`frontend/src/components/settings/MealTypePanel.vue`)

A settings panel for managing meal types:

**Features:**
- **Desktop table:** sortable list with Edit/Delete buttons
- **Mobile cards:** responsive card layout for touch devices
- **Form panel:** slide-up form for creating/editing
- **Validation:** name required, time required
- **Confirmation dialogs:** 
  - Simple delete (if not used)
  - Usage warning (if used in menus)
- **Limits:** "Add" button disabled when reaching 10 custom types
- **Counter:** shows "Custom: N / 10"

**Key methods:**

```typescript
function selectItem(mt: MealType) { /* Open form for edit */ }
function openNew() { /* Open form for create */ }
async function onSave() { /* Validate and save */ }
async function onDelete() { /* Check usage and confirm */ }
async function onConfirmDelete() { /* Execute DELETE */ }
async function onConfirmDeleteUsed() { /* DELETE despite usage */ }
```

**Integration in SettingsView:**

MealTypePanel is rendered as a tab or section in the Settings view, typically alongside other settings panels (FamilyMembersPanel, CategoriesPanel, PreferencesPanel, etc.).

### API Client

**File:** `frontend/src/api/client.ts`

```typescript
async function fetchMealTypes(): Promise<MealType[]> {
  /* GET /meal-types */
}

async function createMealType(data: MealTypeCreate): Promise<MealType> {
  /* POST /meal-types */
}

async function updateMealType(id: number, data: MealTypeCreate): Promise<MealType> {
  /* PUT /meal-types/{id} */
}

async function deleteMealType(id: number): Promise<void> {
  /* DELETE /meal-types/{id} */
}

async function fetchMealTypeUsage(id: number): Promise<MealTypeUsageResponse> {
  /* GET /meal-types/{id}/usage */
}
```

### Type Definitions

**File:** `frontend/src/api/types.ts`

```typescript
export interface MealType {
  id: number
  name: string
  time: string                   // "HH:MM"
  is_system: boolean
  sort_order: number
}

export interface MealTypeCreate {
  name: string
  time: string                   // "HH:MM"
}

export interface MealTypeUsageMenu {
  id: number
  name: string
}

export interface MealTypeUsageResponse {
  meal_type_id: number
  menus: MealTypeUsageMenu[]
  count: number
}
```

## Integration with Menu Slots

### MenuSlotRow Changes

The `MenuSlotRow` ORM model was updated:

**Before (v0.13.1):**
```python
class MenuSlotRow(Base):
    meal_type: Mapped[str]           # Text field: "Завтрак", "Обед", etc.
```

**After (v0.14.0):**
```python
class MenuSlotRow(Base):
    meal_type_id: Mapped[int] = mapped_column(
        ForeignKey("meal_types.id", ondelete="CASCADE"), nullable=False
    )
```

### MenuSlot Entity Integration

The `MenuSlot` domain entity still exists and has a corresponding field updated:

```python
@dataclass
class MenuSlot:
    # ...
    meal_type_id: MealTypeId        # NEW: ID instead of string name
    # ... other fields ...
```

### Repository Layer Changes

Repositories converting MenuSlot ↔ MenuSlotRow must now handle the ID reference:

```python
def _row_to_entity(self, row: MenuSlotRow) -> MenuSlot:
    return MenuSlot(
        # ...
        meal_type_id=MealTypeId(row.meal_type_id),
        # ...
    )

def _make_new_row(self, slot: MenuSlot) -> MenuSlotRow:
    row = MenuSlotRow(
        # ...
        meal_type_id=slot.meal_type_id,
        # ...
    )
    return row
```

## Composition Root Integration

**File:** `backend/composition_root.py`

New wiring in `ApplicationContainer`:

```python
class ApplicationContainer:
    # ... existing dependencies ...

    @property
    def list_meal_types(self) -> ListMealTypes:
        return ListMealTypes(self._meal_type_repo)

    @property
    def create_meal_type(self) -> CreateMealType:
        return CreateMealType(self._meal_type_repo)

    @property
    def update_meal_type(self) -> UpdateMealType:
        return UpdateMealType(self._meal_type_repo)

    @property
    def delete_meal_type(self) -> DeleteMealType:
        return DeleteMealType(self._meal_type_repo)

    @property
    def check_meal_type_usage(self) -> CheckMealTypeUsage:
        return CheckMealTypeUsage(self._meal_type_repo)

    @property
    def create_system_meal_types(self) -> CreateSystemMealTypes:
        return CreateSystemMealTypes(self._meal_type_repo)

    @property
    def _meal_type_repo(self) -> MealTypeRepository:
        return SqlAlchemyMealTypeRepository(self.session)
```

## User Registration Flow Changes

When a new user registers, the registration use case now automatically triggers `CreateSystemMealTypes` to create the three built-in meal types for that user.

**File:** `backend/application/use_cases/auth.py` (RegisterUser or similar)

```python
async def execute(self, user_data: UserRegisterData) -> User:
    # ... create user ...
    user = self._user_repo.save(new_user)
    
    # NEW: Create 3 system meal types
    self._create_system_meal_types.execute(user.id)
    
    # ... rest of registration ...
```

## Error Handling

**New exceptions raised by use cases:**

| Exception | Use Case | HTTP Status | Message |
|-----------|----------|-------------|---------|
| `ValueError` | Create/Update | 400 Bad Request | "Название должно быть от 1 до 50 символов" |
| `DuplicateNameError` | Create/Update | 409 Conflict | "тип приема пищи уже используется" |
| `MealTypeLimitError` | Create | 400 Bad Request | "Достигнут лимит типов приемов пищи (10 пользовательских)" |
| `SystemMealTypeDeletionError` | Delete | 403 Forbidden | "Системные типы приемов пищи нельзя удалить" |
| `AccessDeniedError` | Any with ID | 403 Forbidden | "Тип приема пищи не найден" |

## Testing Strategy

**Unit tests** (in `tests/unit/api/` and domain tests):

- `ListMealTypes`: verify sorting by time, then sort_order, then ID
- `CreateMealType`: test validation (name length, uniqueness, limit), auto-assignment of sort_order
- `UpdateMealType`: test name uniqueness check allowing same name for same ID
- `DeleteMealType`: test system type protection, usage detection
- `CheckMealTypeUsage`: test correct menu references returned
- `CreateSystemMealTypes`: verify 3 types created per user on first call

**API endpoint tests** (in `tests/unit/api/routers/`):

- GET /meal-types: list, sorting, filtering by user
- POST /meal-types: create with valid/invalid data, limits
- PUT /meal-types/{id}: update, name conflict handling
- DELETE /meal-types/{id}: delete, system type protection
- GET /meal-types/{id}/usage: usage checking

**E2E tests** (full scenario):

- User registration → system types created
- Create custom type → added to list
- Edit type → updated in list
- Delete unused type → removed
- Attempt delete system type → error
- Attempt delete used type → warn but allow

## Performance Considerations

- **Sorting:** done in application layer (`ListMealTypes`), not database (no ORDER BY in query)
- **Uniqueness:** enforced by database constraint (`UNIQUE(user_id, name)`)
- **Usage checking:** N+1 avoided by single JOIN query in `get_usage()`
- **Limit checking:** count_custom() uses `COUNT(*)` with filter

## Migration Backward Compatibility

The migration from v0.13.1 to v0.14.0 is **one-way only**:

- **Upgrade:** automatically creates system types and migrates all existing slot references to IDs
- **Downgrade:** theoretically possible via migration downgrade (reverts string names), but menu data integrity may be compromised if custom types were created

No data is lost during upgrade; all existing menus remain functional with their slot references correctly converted to meal type IDs.
