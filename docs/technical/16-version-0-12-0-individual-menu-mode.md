# Version 0.12.0 Features: Individual Menu Planning Mode

**Release date:** 01.02.2026

## Overview

Version 0.12.0 introduces **Individual Menu Planning Mode** (Режим индивидуального планирования меню), allowing different family members to have different dishes in the same weekly menu slot (day + meal type combination). This solves the common problem where family members have different dietary preferences or eating habits.

### Problem Solved

In previous versions, the menu planner operated on a "family-wide" basis: when you added a dish to a specific day/meal slot, it was implicitly for all family members. This made it difficult to plan different meals for different family members at the same meal time (e.g., mum and dad eating borsch while the child eats pasta).

### Solution

- **MenuSlot domain entity** now tracks `member_ids: list[FamilyMemberId]` indicating which family members the dish is planned for.
- **Frontend UI** provides member filtering controls (MemberTagBar) to toggle which family members are active.
- **Slot visibility logic** filters grid display based on active member selection.
- **Automatic portion calculation** uses only the portions of selected family members.
- **Slot merging** groups multiple slots of the same recipe in the same cell with different member subsets.

---

## Feature 1: Domain Model

### MenuSlot Entity

**File:** `backend/domain/entities/menu.py`

The `MenuSlot` dataclass now includes:

```python
@dataclass
class MenuSlot:
    day: int                                    # 0–6 (Mon–Sun)
    meal_type: str
    recipe_id: RecipeId | None = None
    product_id: ProductId | None = None
    quantity: float | None = None
    unit: str | None = None
    servings_override: float | None = None
    pieces_override: int | None = None
    position: int = 0
    member_ids: list[FamilyMemberId] = field(default_factory=list)
```

**Field semantics:**
- `member_ids` — list of family member IDs this slot is planned for.
- Empty list means **no member restriction** (dish is for everyone, backward-compatible).
- Non-empty list means **dish is only for these specific members**.

### WeeklyMenu Logic Update

**File:** `backend/domain/entities/menu.py`

The `_same_item()` method now considers `member_ids` when determining if two slots represent the same item:

```python
@staticmethod
def _same_item(existing: MenuSlot, new: MenuSlot) -> bool:
    if existing.day != new.day or existing.meal_type != new.meal_type:
        return False
    if new.product_id is not None and existing.product_id == new.product_id:
        return True  # Products don't have member_ids, upsert by product_id alone
    if new.recipe_id is not None and existing.recipe_id == new.recipe_id:
        # Recipes: same item only if member_ids are identical
        return sorted(existing.member_ids) == sorted(new.member_ids)
    return False
```

**Implication:** two recipe slots with the same recipe_id but different member_ids are treated as **different items**, allowing multiple slots for the same recipe targeting different members in the same cell.

---

## Feature 2: Database Migration

**File:** `backend/infrastructure/database/migrations/versions/a9b8c7d6e5f4_add_member_ids_to_menu_slots.py`

Migration adds JSON column to store member IDs:

```python
op.add_column(
    "menu_slots",
    sa.Column(
        "member_ids",
        sa.String(),
        nullable=False,
        server_default="[]",  # Default empty list (backward compatible)
    ),
)
```

**Details:**
- Column name: `member_ids`
- Type: `String` (stores JSON array as text, e.g., `"[1, 2]"`)
- Nullable: False
- Default: `"[]"` (empty array)

**Backward compatibility:** existing slots default to empty array, meaning they have no member restriction.

---

## Feature 3: API Layer

### Request/Response Schemas

**File:** `backend/api/schemas/menu.py`

```python
class MenuSlotSchema(BaseModel):
    day: int
    meal_type: str
    recipe_id: int | None = None
    product_id: int | None = None
    quantity: float | None = None
    unit: str | None = None
    servings_override: float | None = None
    pieces_override: int | None = None
    position: int = 0
    member_ids: list[int] = []  # List of family member IDs
```

**Semantics in API:**
- `member_ids` is a list of family member IDs.
- Empty list `[]` means no member restriction (dish for everyone).
- Non-empty list means dish is restricted to those members.

### API Converters

**File:** `backend/api/converters.py`

Converters handle serialization/deserialization of `member_ids`:

```python
# Domain → Schema
slot_schema = MenuSlotSchema(
    day=domain_slot.day,
    meal_type=domain_slot.meal_type,
    recipe_id=domain_slot.recipe_id,
    product_id=domain_slot.product_id,
    member_ids=domain_slot.member_ids,
    # ... other fields
)

# Schema → Domain
domain_slot = MenuSlot(
    day=schema.day,
    meal_type=schema.meal_type,
    recipe_id=schema.recipe_id,
    product_id=schema.product_id,
    member_ids=schema.member_ids,
    # ... other fields
)
```

---

## Feature 4: Frontend UI Components

### MemberTagBar Component

**File:** `frontend/src/components/planner/MemberTagBar.vue`

Displays member filtering controls:

```vue
<script setup lang="ts">
import MemberTag from './MemberTag.vue'
import type { FamilyMember } from '@/api/types'

defineProps<{
  members: FamilyMember[]
  activeMemberIds: Set<number>
  allActive: boolean
  activePortionsLabel: string
}>()

defineEmits<{
  'toggle-member': [id: number]
  'toggle-all': []
}>()
</script>

<template>
  <div
    v-if="members.length > 0"
    role="toolbar"
    aria-label="Фильтр по членам семьи"
    class="flex items-center gap-2 overflow-x-auto scrollbar-none snap-x snap-mandatory px-0 py-1"
  >
    <!-- "All" button -->
    <MemberTag
      label="Все"
      :active="allActive"
      :special="true"
      :title="allActive ? 'Показать только общие' : 'Включить всех участников'"
      class="snap-start"
      @toggle="$emit('toggle-all')"
    />
    <div class="w-px h-5 bg-gray-300 shrink-0" />
    
    <!-- Individual member buttons -->
    <MemberTag
      v-for="member in members"
      :key="member.id"
      :label="`${member.name} ×${member.portion_multiplier}`"
      :active="activeMemberIds.has(member.id)"
      :title="activeMemberIds.has(member.id) ? `Нажмите, чтобы исключить ${member.name}` : `Нажмите, чтобы включить ${member.name}`"
      class="snap-start"
      @toggle="$emit('toggle-member', member.id)"
    />
    
    <!-- Active portions label -->
    <span class="ml-auto text-xs text-gray-500 whitespace-nowrap shrink-0">
      {{ activePortionsLabel }}
    </span>
  </div>
</template>
```

**Features:**
- "Все" (All) button to toggle all members at once.
- Individual member buttons showing name and portion multiplier.
- Horizontal scroll support for many family members.
- Active portions label showing current selection summary.
- Accessibility: `aria-label`, `aria-live` for screen readers.

### MemberTag Component

**File:** `frontend/src/components/planner/MemberTag.vue`

Individual toggle button for a member or "All":

```vue
<script setup lang="ts">
defineProps<{
  label: string
  active: boolean
  special?: boolean  // "All" button styling
  title?: string     // Tooltip
}>()

defineEmits<{
  toggle: []
}>()
</script>
```

Renders as a clickable chip/button with active/inactive styling.

### MenuPlannerView State Management

**File:** `frontend/src/views/MenuPlannerView.vue`

Member filtering logic:

```typescript
// Reactive state
const activeMemberIds = ref<Set<number>>(new Set())

// Computed properties
const allActive = computed(() =>
  familyStore.items.length > 0 &&
  familyStore.items.every(m => activeMemberIds.value.has(m.id))
)

const activePortions = computed(() => {
  const active = familyStore.items.filter(m => activeMemberIds.value.has(m.id))
  if (active.length === 0) return totalFamilyPortions.value
  return active.reduce((sum, m) => sum + m.portion_multiplier, 0)
})

const activePortionsLabel = computed(() => {
  const active = familyStore.items.filter(m => activeMemberIds.value.has(m.id))
  if (active.length === 0) return '0 (никто не выбран)'
  if (allActive.value) return `${activePortions.value.toFixed(1)} порции (все)`
  const names = active.map(m => m.name).join(', ')
  return `${activePortions.value.toFixed(1)} порции (${names})`
})

// Initialize with all family members
watch(
  () => familyStore.items,
  (members) => {
    activeMemberIds.value = new Set(members.map(m => m.id))
  },
  { immediate: true }
)

// Reset on menu switch
watch(
  () => menuStore.selectedId,
  () => {
    activeMemberIds.value = new Set(familyStore.items.map(m => m.id))
  }
)

// Toggle handlers
function toggleMember(id: number) {
  const next = new Set(activeMemberIds.value)
  if (next.has(id)) {
    next.delete(id)
  } else {
    next.add(id)
  }
  activeMemberIds.value = next
}

function toggleAll() {
  if (allActive.value) {
    activeMemberIds.value = new Set()
  } else {
    activeMemberIds.value = new Set(familyStore.items.map(m => m.id))
  }
}
```

### Adding a Dish for Subset of Members

When adding a recipe with a subset of members selected:

```typescript
async function onAddItem(day: number, mealType: string, data: { type: 'recipe' | 'product'; id: number }) {
  await menuStore.ensureMenuSelected()

  // Determine if recipe is for a subset of members
  const isSubset = data.type === 'recipe' &&
    activeMemberIds.value.size > 0 &&
    !allActive.value &&
    familyStore.items.length > 0

  // Populate member_ids if subset
  const memberIdsForSlot = isSubset ? [...activeMemberIds.value] : []
  
  // Calculate servings based on active members
  const servingsForSlot = data.type === 'recipe'
    ? (activeMemberIds.value.size === 0 ? totalFamilyPortions.value : activePortions.value)
    : null

  const slot: MenuSlot = {
    day,
    meal_type: mealType,
    recipe_id: data.type === 'recipe' ? data.id : null,
    product_id: data.type === 'product' ? data.id : null,
    unit: data.type === 'product' ? productStore.allItems.find(p => p.id === data.id)?.recipe_unit ?? null : null,
    quantity: data.type === 'product' ? ... : null,
    servings_override: servingsForSlot,
    member_ids: memberIdsForSlot,  // Set member_ids for subset
  }
  await menuStore.addSlotToMenu(slot)
  
  // Toast notification
  if (data.type === 'recipe' && isSubset) {
    const recipeName = recipeNames.value[data.id] ?? `#${data.id}`
    const memberNames = familyStore.items
      .filter(m => activeMemberIds.value.has(m.id))
      .map(m => m.name)
    toast.show(`${recipeName}: ${activePortions.value.toFixed(1)} порции (${memberNames.join(', ')})`, 'success')
  }
}
```

**Logic:**
- If recipe is added with a subset of members (not all, not empty): populate `member_ids`.
- Servings calculated from `activePortions` (sum of portion multipliers of selected members).
- Toast notification shows recipe name, portions, and member list.

---

## Feature 5: Grid Filtering and Merging

### Slot Visibility Utility

**File:** `frontend/src/utils/slotVisibility.ts`

```typescript
export function isSlotVisible(slot: MenuSlot, activeIds: Set<number>): boolean {
  if (!slot.member_ids?.length) return true  // No restriction: always visible
  return slot.member_ids.some(id => activeIds.has(id))  // Visible if any member matches
}

export function getMemberInitials(
  memberIds: number[],
  familyMembers: { id: number; name: string }[]
): string[] {
  if (!memberIds.length) return []
  const initials = memberIds.map(id => {
    const member = familyMembers.find(m => m.id === id)
    return member ? member.name.charAt(0).toUpperCase() : '?'
  })
  // Handle duplicate initials: use 2 chars
  const seen = new Map<string, number>()
  return initials.map((ini, idx) => {
    const count = (seen.get(ini) ?? 0) + 1
    seen.set(ini, count)
    if (initials.filter(i => i === ini).length > 1) {
      const member = familyMembers.find(m => m.id === memberIds[idx])
      return member ? member.name.substring(0, 2) : ini
    }
    return ini
  })
}
```

**Visibility logic:**
- Empty `member_ids` → visible to everyone (backward compatible).
- Non-empty `member_ids` → visible only if any of its members are in `activeIds`.

**Member initials:**
- Extracts first character of each member's name.
- If multiple members share the same initial, uses first 2 characters for clarity.

### GridCell Filtering and Merging

**File:** `frontend/src/components/planner/GridCell.vue`

Slot filtering and merging logic:

```typescript
const rawCellSlots = computed(() =>
  props.slots
    .filter((s) => s.day === props.day && s.meal_type === props.mealType)
    .sort((a, b) => (a.position ?? 0) - (b.position ?? 0)),
)

const cellSlots = computed((): CellItem[] => {
  const activeIds = props.activeMemberIds
  if (!activeIds || activeIds.size === 0) {
    // No filter active — show all but still merge grouped slots
    return mergeSameRecipeSlots(rawCellSlots.value)
  }
  const visible = rawCellSlots.value.filter(s => isSlotVisible(s, activeIds))
  return mergeSameRecipeSlots(visible)
})

function mergeSameRecipeSlots(slots: MenuSlot[]): CellItem[] {
  const groups = new Map<number, MenuSlot[]>()
  const result: CellItem[] = []
  
  for (const slot of slots) {
    if (!slot.recipe_id || !slot.member_ids?.length) {
      // Products or recipes without member restriction: don't merge
      result.push(slot)
      continue
    }
    
    // Group recipe slots with member_ids by recipe_id
    const existing = groups.get(slot.recipe_id)
    if (existing) existing.push(slot)
    else groups.set(slot.recipe_id, [slot])
  }
  
  // Convert groups to CellItem
  for (const [recipeId, group] of groups) {
    if (group.length === 1) {
      result.push(group[0]!)
    } else {
      // Multiple slots: create MergedSlotView
      result.push({
        _merged: true,
        recipe_id: recipeId,
        slots: group,
        totalServings: group.reduce((sum, s) => sum + (s.servings_override ?? 0), 0),
        allMemberIds: [...new Set(group.flatMap(s => s.member_ids ?? []))],
      } as MergedSlotView)
    }
  }
  
  return result
}
```

**Filtering logic:**
1. Extract slots for this cell (`day` × `meal_type`).
2. If no filter active: show all slots from this cell.
3. If filter active: show only slots where `isSlotVisible()` returns true.

**Merging logic:**
1. Slots without `member_ids` (products, general recipes) are added as-is.
2. Slots with `member_ids` are grouped by `recipe_id`.
3. Single-slot groups are added as regular slots.
4. Multi-slot groups are converted to `MergedSlotView` with:
   - `totalServings` — sum of servings from all slots.
   - `allMemberIds` — union of all member IDs across slots.

---

## Feature 6: MergedSlotView Type

**File:** `frontend/src/api/types.ts`

```typescript
export interface MergedSlotView {
  _merged: true
  recipe_id: number
  slots: MenuSlot[]
  totalServings: number
  allMemberIds: number[]
}

export function isMergedSlot(item: CellItem): item is MergedSlotView {
  return typeof item === 'object' && '_merged' in item && item._merged === true
}
```

**Usage:** allows components to distinguish between regular `MenuSlot` and merged view in grid cells.

### MergedSlotDialog

When user clicks a MergedSlotView, a dialog opens showing all slots and allowing individual slot editing/deletion:

```typescript
function openMergedDialog(merged: MergedSlotView) {
  mergedDialogSlot.value = merged
  showMergedDialog.value = true
}

function onMergedEditSlot(slot: MenuSlot) {
  showMergedDialog.value = false
  emit('editItem', slot)  // Open edit dialog for single slot
}

function onMergedRemoveSlot(slot: MenuSlot) {
  showMergedDialog.value = false
  emit('removeItem', { recipe_id: slot.recipe_id, product_id: slot.product_id, position: slot.position ?? null })
}
```

---

## Feature 7: Mobile Adaptation

The MemberTagBar is adapted for touch interaction on mobile devices:

- **Touch-friendly buttons:** minimum 40px size for comfortable finger tapping.
- **Horizontal scroll:** if many family members, panel scrolls horizontally (snap scrolling for better UX).
- **Responsive layout:** adapts to screen width, hiding inactive members if space is limited.

---

## Testing Strategy

### Domain Tests

**File:** `tests/unit/domain/test_menu_slot.py`

Tests for `MenuSlot` and `WeeklyMenu`:

```python
def test_menu_slot_with_member_ids():
    slot = MenuSlot(
        day=0,
        meal_type='Завтрак',
        recipe_id=RecipeId(1),
        member_ids=[FamilyMemberId(1), FamilyMemberId(2)],
    )
    assert slot.member_ids == [FamilyMemberId(1), FamilyMemberId(2)]

def test_same_item_considers_member_ids():
    slot1 = MenuSlot(day=0, meal_type='Завтрак', recipe_id=RecipeId(1), member_ids=[FamilyMemberId(1)])
    slot2 = MenuSlot(day=0, meal_type='Завтрак', recipe_id=RecipeId(1), member_ids=[FamilyMemberId(2)])
    # Different member_ids: not the same item
    assert not WeeklyMenu._same_item(slot1, slot2)

def test_same_item_ignores_member_ids_for_products():
    slot1 = MenuSlot(day=0, meal_type='Завтрак', product_id=ProductId(1))
    slot2 = MenuSlot(day=0, meal_type='Завтрак', product_id=ProductId(1))
    # Products: same item (member_ids don't apply)
    assert WeeklyMenu._same_item(slot1, slot2)
```

### API Integration Tests

**File:** `tests/unit/api/test_menu_router.py`

Tests for API endpoints:

```python
def test_add_slot_with_member_ids(client, app_context):
    # Arrange
    response = client.post('/api/menus', json={'name': 'Test Menu'})
    menu_id = response.json()['id']
    
    # Act: add slot with member_ids
    response = client.post(
        f'/api/menus/{menu_id}/slots',
        json={
            'day': 0,
            'meal_type': 'Завтрак',
            'recipe_id': 1,
            'member_ids': [1, 2],
        }
    )
    
    # Assert
    assert response.status_code == 201
    assert response.json()['member_ids'] == [1, 2]

def test_get_menu_includes_member_ids(client, app_context):
    # Verify member_ids are returned in menu response
    response = client.get(f'/api/menus/{menu_id}')
    menu = response.json()
    assert all('member_ids' in slot for slot in menu['slots'])
```

### Frontend Component Tests

**File:** `frontend/src/components/planner/__tests__/MemberTagBar.spec.ts`

Tests for MemberTagBar component:

```typescript
import { mount } from '@vue/test-utils'
import MemberTagBar from '../MemberTagBar.vue'

describe('MemberTagBar', () => {
  it('renders member buttons with portion multipliers', () => {
    const wrapper = mount(MemberTagBar, {
      props: {
        members: [
          { id: 1, name: 'Мама', portion_multiplier: 1.0 },
          { id: 2, name: 'Ребёнок', portion_multiplier: 0.5 },
        ],
        activeMemberIds: new Set([1, 2]),
        allActive: true,
        activePortionsLabel: '1.5 порции (все)',
      },
    })

    expect(wrapper.text()).toContain('Мама ×1')
    expect(wrapper.text()).toContain('Ребёнок ×0.5')
    expect(wrapper.text()).toContain('1.5 порции (все)')
  })

  it('emits toggle-member when member button clicked', async () => {
    const wrapper = mount(MemberTagBar, { ... })
    // Click member button
    expect(wrapper.emitted('toggle-member')).toBeTruthy()
  })
})
```

---

## Example Usage Scenarios

### Scenario 1: Different Dishes for Family Members

1. Open Menu Planner.
2. Select family members from MemberTagBar (e.g., "мама" and "папа").
3. Drag "Борщ" to Monday Lunch.
4. System adds borsch for mum and dad with calculated portions (2.0).
5. Select only "ребёнок" from MemberTagBar.
6. Drag "Макаронник" to Monday Lunch.
7. System adds pasta for child with 0.5 portions.
8. In grid: both dishes visible in Monday Lunch cell, grouped or separate depending on UI implementation.
9. When viewing menu:
   - Select "мама" + "папа" → see borsch only.
   - Select "ребёнок" → see pasta only.
   - Select all → see both.

### Scenario 2: Mixed Dietary Needs

1. Mum has vegetarian preference, dad and child eat everything.
2. Monday dinner:
   - Add "Овощное рагу" with "мама" → 1.0 portion.
   - Add "Котлеты" with "папа" + "ребёнок" → 1.5 portions.
3. When filtering:
   - Show "мама" → only stew visible.
   - Show "папа" + "ребёнок" → only cutlets visible.

---

## Backward Compatibility

- **Existing menus:** slots without `member_ids` (empty array) are treated as "for everyone", maintaining backward compatibility.
- **Products:** product slots don't use `member_ids` (irrelevant for portions of individual items).
- **API:** `member_ids` defaults to `[]`, making it optional in requests.

---

## Known Limitations

1. **Member initials collision:** if multiple members share the same name start, using 2-char initials. User can see full name in tooltip.
2. **Merging logic:** currently merges only recipes with non-empty `member_ids` in the same cell. Products are not merged (less common use case).
3. **Portion override:** when editing a merged slot, portions are per-slot, not merged total (user must manage individually).
