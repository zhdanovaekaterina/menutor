# v0.10.0 — Сортировка приёмов пищи и трёхрежимная мобильная навигация планировщика

**Дата:** 25.03.2026

Версия 0.10.0 добавляет сортировку приёмов пищи в экране сводки блюд, а также полностью переконфигурирует мобильную навигацию планировщика меню с поддержкой трёх интерактивных режимов (Неделя, День, Приём пищи) вместо прежней горизонтальной прокрутки.

---

## Обзор функций

1. **Сортировка приёмов пищи в сводке блюд** — приёмы пищи теперь отображаются в порядке: сначала по дню недели (Пн→Вс), затем по типу приёма (Завтрак→Обед→Ужин)
2. **Режим Неделя на мобильных устройствах** — 7 тапаемых карточек дней недели с миниатюрой меню и счётчиком приёмов пищи
3. **Режим День на мобильных устройствах** — полноэкранный вид с тремя блюдами (Завтрак, Обед, Ужин) для выбранного дня, каждое занимает равную высоту
4. **Режим Приём пищи на мобильных устройствах** — полноэкранный GridCell с двухосевой жестовой навигацией (горизонтальный свайп = смена дня, вертикальный свайп = смена приёма пищи)
5. **Анимированные переходы между режимами** — zoom (Неделя↔День), drill (День↔Приём пищи), bounce на границах
6. **Композable useSwipeGesture** — переиспользуемый компонент для обработки touch событий с поддержкой двухосевого свайпа
7. **Сброс режима при смене меню** — переключение на другое меню возвращает в режим Неделя
8. **Доступность** — aria-live регион для объявления текущего режима и позиции

---

## Архитектура

### Слой представления (Vue 3 компоненты)

**Директория:** `frontend/src/components/` и `frontend/src/composables/`

#### Новые компоненты

| Компонент | Файл | Назначение |
|-----------|------|-----------|
| **MobileGridNavigator** | `components/planner/MobileGridNavigator.vue` | Контейнер и оркестратор трёх режимов навигации (управляет состоянием режима и дня) |
| **MobileWeekView** | `components/planner/MobileWeekView.vue` | Отображение 7 карточек дней недели с тапом для перехода в День |
| **MobileDayView** | `components/planner/MobileDayView.vue` | Полноэкранный вид с 3 секциями приёмов пищи (Завтрак/Обед/Ужин) с равной высотой |
| **MobileMealView** | `components/planner/MobileMealView.vue` | Полноэкранный GridCell с двухосевым свайпом, стрелочные кнопки для смены дня/приёма |
| **WeekDayCard** | `components/planner/WeekDayCard.vue` | Карточка одного дня (аббревиатура, счётчик, текстовое резюме приёмов) |
| **ModeBackButton** | `components/planner/ModeBackButton.vue` | Кнопка-навигатор (← День, ← Неделя) с aria-label |
| **IconChevronUp** | `components/ui/icons/IconChevronUp.vue` | SVG иконка шеврона для вверх/вниз навигации |

#### Обновлённые компоненты

| Компонент | Файл | Изменение |
|-----------|------|-----------|
| **GridCell** | `components/planner/GridCell.vue` | Новый пропс `size: 'normal' \| 'medium' \| 'full'` для различных режимов отображения (нормальный, средний, полноэкранный) |
| **PlannerGrid** | `components/planner/PlannerGrid.vue` | На мобильных устройствах вместо snap-scroll контейнера теперь используется MobileGridNavigator |
| **main.css** | `frontend/src/main.css` | Новые классы анимаций: `.zoom-enter-active`, `.zoom-leave-active`, `.drill-enter-active`, `.drill-leave-active`, `.bounce-animation` |

#### Новый composable: useSwipeGesture

**Файл:** `frontend/src/composables/useSwipeGesture.ts`

```typescript
interface SwipeGestureConfig {
  onSwipeLeft?: () => void
  onSwipeRight?: () => void
  onSwipeUp?: () => void
  onSwipeDown?: () => void
  threshold?: number        // минимальное расстояние для регистрации свайпа (пиксели)
  verticalThreshold?: number // опциональный отдельный threshold для вертикального свайпа
}

export function useSwipeGesture(
  element: Ref<HTMLElement | null>,
  config: SwipeGestureConfig
): void
```

**Интерфейс:**

```typescript
// В компоненте (например, MobileMealView.vue):
const containerRef = ref<HTMLElement | null>(null)

useSwipeGesture(containerRef, {
  onSwipeLeft: () => goToNextDay(),
  onSwipeRight: () => goToPreviousDay(),
  onSwipeUp: () => goToNextMeal(),
  onSwipeDown: () => goToPreviousMeal(),
  threshold: 50
})
```

**Реализация:**

- Слушает `touchstart`, `touchmove`, `touchend` события на элементе
- Вычисляет дельту X и Y
- Регистрирует свайп, если абсолютное расстояние превышает `threshold`
- Игнорирует противоположные направления (если вертикальная дельта больше горизонтальной, свайп вертикальный)
- Работает на сенсорных устройствах и планшетах

#### MobileGridNavigator (контейнер состояния)

**Пропсы:**

```typescript
interface Props {
  currentDayIndex: number  // 0-6
  currentMealIndex: number // 0-2
}

interface Emits {
  'update:currentDayIndex': [value: number]
  'update:currentMealIndex': [value: number]
  'update:mode': [mode: 'week' | 'day' | 'meal']
}
```

**Состояние:**

```typescript
const mode = ref<'week' | 'day' | 'meal'>('week')
const currentDayIndex = ref(0)  // 0-6 (пн-вс)
const currentMealIndex = ref(0) // 0-2 (завтрак, обед, ужин)
```

**Логика:**

- При переключении меню (смена `currentMenuId`) мод сбрасывается в 'week' и индексы в 0
- Переходы между модами:
  - **Неделя → День:** при тапе на WeekDayCard устанавливаем `mode = 'day'` и `currentDayIndex` тапнутого дня
  - **День → Приём:** при тапе на заголовок приёма пищи устанавливаем `mode = 'meal'` и `currentMealIndex`
  - **Приём → День:** кнопка-вернуться устанавливает `mode = 'day'`
  - **День → Неделя:** кнопка-вернуться устанавливает `mode = 'week'`

**Граничные условия:**

- При свайпе влево-вправо на последний/первый день — bounce анимация (отскок, возврат к краю)
- При свайпе вверх-вниз на последний/первый приём пищи — bounce анимация

#### MobileWeekView (режим Неделя)

**Пропсы:**

```typescript
interface Props {
  days: DayOfWeek[]     // ['Пн', 'Вт', ..., 'Вс']
  menuItems: GridItem[] // все элементы текущего меню
}

interface Emits {
  'select-day': [dayIndex: number]
}
```

**Структура:**

```vue
<template>
  <div class="mobile-week-view">
    <div class="week-grid">
      <WeekDayCard
        v-for="(day, index) in days"
        :key="index"
        :day="day"
        :item-count="getItemCountForDay(index)"
        :meal-summary="getMealSummary(index)"
        @click="$emit('select-day', index)"
      />
    </div>
  </div>
</template>
```

**Карточка дня (WeekDayCard):**

- **Аббревиатура дня:** пн, вт, ср, чт, пт, сб, вс
- **Счётчик:** X приёмов (число элементов в день)
- **Текстовое резюме:** например, «Завтрак, Обед, Ужин» или «Завтрак, Ужин»
- **Тап:** переход в День

#### MobileDayView (режим День)

**Пропсы:**

```typescript
interface Props {
  selectedDayIndex: number
  mealTypes: MealType[]    // ['Завтрак', 'Обед', 'Ужин']
  gridItems: GridItem[]
}

interface Emits {
  'select-meal': [mealIndex: number]
  'back': []
  'prev-day': []
  'next-day': []
}
```

**Структура:**

```vue
<template>
  <div class="mobile-day-view">
    <!-- Заголовок -->
    <div class="day-header">
      <ModeBackButton mode="day" @click="$emit('back')" />
      <h2>{{ dayName }}</h2>
      <div class="day-indicators">{{ selectedDayIndex + 1 }}/7</div>
    </div>

    <!-- Три равные секции приёмов -->
    <div class="meals-container">
      <div
        v-for="(meal, idx) in mealTypes"
        :key="idx"
        class="meal-section"
        @click="$emit('select-meal', idx)"
      >
        <div class="meal-header">{{ meal }}</div>
        <GridCell :size="'medium'" :items="getItemsForMeal(idx)" />
      </div>
    </div>

    <!-- Навигация дней -->
    <div class="day-nav">
      <button @click="$emit('prev-day')" :disabled="selectedDayIndex === 0">←</button>
      <div class="dots">
        <span v-for="i in 7" :key="i" :class="{ active: i === selectedDayIndex + 1 }" />
      </div>
      <button @click="$emit('next-day')" :disabled="selectedDayIndex === 6">→</button>
    </div>
  </div>
</template>
```

**Особенности:**

- Три секции (Завтрак, Обед, Ужин) делят экран поровну (каждая ~33% высоты)
- Заголовок приёма пищи тапаемый → переход в Приём пищи
- 7 точек снизу показывают текущий день
- Стрелки левой/правой навигации на месте, но отключены на границах (первый/последний день)

#### MobileMealView (режим Приём пищи)

**Пропсы:**

```typescript
interface Props {
  selectedDayIndex: number
  selectedMealIndex: number
  mealTypes: MealType[]
  gridItems: GridItem[]
}

interface Emits {
  'back': []
  'prev-day': []
  'next-day': []
  'prev-meal': []
  'next-meal': []
}
```

**Структура:**

```vue
<template>
  <div class="mobile-meal-view">
    <!-- Навигационная панель (сверху) -->
    <div class="meal-nav-header">
      <ModeBackButton mode="meal" @click="$emit('back')" />
      <h2>{{ currentMealName }}</h2>
      <!-- Индикаторы дня и приёма пищи -->
      <div class="indicators">
        <span class="day-indicator">{{ selectedDayIndex + 1 }}/7</span>
        <span class="meal-indicator">{{ selectedMealIndex + 1 }}/3</span>
      </div>
    </div>

    <!-- Основной контент (полноэкранный GridCell) -->
    <div
      ref="containerRef"
      class="meal-container"
      role="region"
      aria-live="polite"
      :aria-label="`Приём пищи: ${currentMealName}, День: ${dayName}`"
    >
      <GridCell
        :size="'full'"
        :items="getItemsForMeal()"
        :allow-drag="true"
      />
    </div>

    <!-- Нижняя навигация (вверх/вниз для приёмов, влево/вправо для дней) -->
    <div class="meal-footer-nav">
      <!-- Кнопка вверх для предыдущего приёма пищи -->
      <button
        :disabled="selectedMealIndex === 0"
        @click="$emit('prev-meal')"
        :aria-label="`Предыдущий приём пищи`"
      >
        <IconChevronUp class="rotate-180" />
      </button>

      <!-- Кнопка вниз для следующего приёма пищи -->
      <button
        :disabled="selectedMealIndex === 2"
        @click="$emit('next-meal')"
        :aria-label="`Следующий приём пищи`"
      >
        <IconChevronUp />
      </button>

      <!-- Дни навигация -->
      <div class="day-nav-row">
        <button
          :disabled="selectedDayIndex === 0"
          @click="$emit('prev-day')"
          aria-label="Предыдущий день"
        >
          ←
        </button>
        <div class="dots">
          <span v-for="i in 7" :key="i" :class="{ active: i === selectedDayIndex + 1 }" />
        </div>
        <button
          :disabled="selectedDayIndex === 6"
          @click="$emit('next-day')"
          aria-label="Следующий день"
        >
          →
        </button>
      </div>
    </div>

    <!-- Aria-live регион -->
    <div aria-live="polite" aria-atomic="true" class="sr-only">
      {{ currentMealName }} в {{ dayName }}
    </div>
  </div>
</template>
```

**Жестовая навигация (через useSwipeGesture):**

```typescript
useSwipeGesture(containerRef, {
  onSwipeLeft: () => goToNextDay(),    // свайп влево = след. день
  onSwipeRight: () => goToPreviousDay(), // свайп вправо = пред. день
  onSwipeUp: () => goToNextMeal(),     // свайп вверх = след. приём
  onSwipeDown: () => goToPreviousMeal(), // свайп вниз = пред. приём
  threshold: 50
})
```

#### Сортировка приёмов пищи (Meal Summary)

**Файлы:** `components/shopping/MealCard.vue`, `components/shopping/StandaloneProductCard.vue`

**Логика сортировки:**

```typescript
const sortedMeals = computed(() => {
  return [...meals.value].sort((a, b) => {
    // Сначала по дню недели (пн=0, вс=6)
    const dayDiff = a.dayOfWeek - b.dayOfWeek
    if (dayDiff !== 0) return dayDiff

    // Затем по типу приёма (завтрак=0, обед=1, ужин=2)
    const mealTypeOrder = { 'Завтрак': 0, 'Обед': 1, 'Ужин': 2 }
    return (mealTypeOrder[a.mealType] ?? 999) - (mealTypeOrder[b.mealType] ?? 999)
  })
})
```

**Примеры порядка:**

- Пн - Завтрак
- Пн - Обед
- Пн - Ужин
- Вт - Завтрак
- Вт - Обед
- ...
- Вс - Ужин

---

### Слой приложения (Use Cases)

**Директория:** `backend/application/use_cases/`

Нет новых use cases. Все изменения касаются фронтенда.

---

### Слой домена (Domain)

Нет изменений.

---

### API слой

Нет новых эндпоинтов. API остаётся совместим с v0.9.1.

---

## CSS Анимации

**Файл:** `frontend/src/main.css`

### Zoom (Неделя ↔ День)

```css
.zoom-enter-active,
.zoom-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.zoom-enter-from {
  opacity: 0;
  transform: scale(0.8);
}

.zoom-leave-to {
  opacity: 0;
  transform: scale(1.2);
}
```

### Drill (День ↔ Приём пищи)

```css
.drill-enter-active,
.drill-leave-active {
  transition: opacity 0.4s ease, transform 0.4s ease;
}

.drill-enter-from {
  opacity: 0;
  transform: translateX(100%);
}

.drill-leave-to {
  opacity: 0;
  transform: translateX(-100%);
}
```

### Bounce (Граничные условия)

```css
@keyframes bounce {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(10px); }
  75% { transform: translateX(-10px); }
}

.bounce-animation {
  animation: bounce 0.4s ease-out;
}
```

---

## Маршруты и навигация

**Файл:** `frontend/src/router/index.ts`

Нет новых маршрутов. Навигация перемещается на уровне компонента (MobileGridNavigator).

---

## Состояние (Pinia)

**Файл:** `frontend/src/stores/menus.ts` (изменение логики сброса режима)

```typescript
function selectMenu(menuId: MenuId): void {
  selectedMenuId.value = menuId

  // Сбросить режим мобильной навигации при смене меню
  if (process.client) {
    const gridNavigatorState = localStorage.getItem('gridNavigatorState')
    if (gridNavigatorState) {
      const state = JSON.parse(gridNavigatorState)
      state.mode = 'week'
      state.currentDayIndex = 0
      state.currentMealIndex = 0
      localStorage.setItem('gridNavigatorState', JSON.stringify(state))
    }
  }
}
```

---

## Доступность (a11y)

### aria-live в MobileMealView

```vue
<div aria-live="polite" aria-atomic="true" class="sr-only">
  {{ currentMealName }} в {{ dayName }}
</div>
```

Объявляет текущий приём пищи и день при навигации (для скрин-ридеров).

### aria-label на кнопках

```vue
<button
  @click="goToNextDay()"
  aria-label="Следующий день"
>
  →
</button>
```

### role на контейнере

```vue
<div role="region" aria-label="Сетка меню">
  <GridCell ... />
</div>
```

---

## Тестирование

### Unit тесты Vue компонентов

**Директория:** `tests/unit/components/`

#### test_mobile_grid_navigator.ts

```typescript
import { mount } from '@vue/test-utils'
import MobileGridNavigator from '@/components/planner/MobileGridNavigator.vue'

describe('MobileGridNavigator', () => {
  it('should initialize in week mode', () => {
    const wrapper = mount(MobileGridNavigator, {
      props: { currentDayIndex: 0, currentMealIndex: 0 }
    })

    expect(wrapper.vm.mode).toBe('week')
  })

  it('should transition to day mode on day select', async () => {
    const wrapper = mount(MobileGridNavigator)
    await wrapper.vm.selectDay(2)

    expect(wrapper.vm.mode).toBe('day')
    expect(wrapper.vm.currentDayIndex).toBe(2)
  })

  it('should bounce animation on last day swipe right', async () => {
    const wrapper = mount(MobileGridNavigator)
    await wrapper.vm.setCurrentDayIndex(6) // последний день

    const result = wrapper.vm.goToNextDay()
    expect(result.bounceAnimation).toBe(true)
  })

  it('should reset mode to week on menu switch', async () => {
    const wrapper = mount(MobileGridNavigator, {
      props: { currentMenuId: '1' }
    })
    await wrapper.vm.setMode('meal')

    await wrapper.setProps({ currentMenuId: '2' })

    expect(wrapper.vm.mode).toBe('week')
  })
})
```

#### test_mobile_meal_view.ts

```typescript
import { mount } from '@vue/test-utils'
import MobileMealView from '@/components/planner/MobileMealView.vue'

describe('MobileMealView', () => {
  it('should register swipe left to next day', async () => {
    const wrapper = mount(MobileMealView, {
      props: {
        selectedDayIndex: 0,
        selectedMealIndex: 0,
        mealTypes: ['Завтрак', 'Обед', 'Ужин'],
        gridItems: []
      }
    })

    // Симулировать swipe left
    const container = wrapper.find('.meal-container')
    await container.trigger('touchstart', {
      touches: [{ clientX: 100, clientY: 100 }]
    })
    await container.trigger('touchmove', {
      touches: [{ clientX: 50, clientY: 100 }]
    })
    await container.trigger('touchend')

    expect(wrapper.emitted('next-day')).toBeTruthy()
  })

  it('should disable prev-day button on first day', () => {
    const wrapper = mount(MobileMealView, {
      props: {
        selectedDayIndex: 0,
        selectedMealIndex: 0,
        mealTypes: ['Завтрак', 'Обед', 'Ужин'],
        gridItems: []
      }
    })

    const prevButton = wrapper.find('.meal-footer-nav button:first-child')
    expect(prevButton.attributes('disabled')).toBeDefined()
  })
})
```

#### test_use_swipe_gesture.ts

```typescript
import { useSwipeGesture } from '@/composables/useSwipeGesture'
import { ref } from 'vue'

describe('useSwipeGesture', () => {
  it('should detect left swipe', () => {
    const element = ref<HTMLElement>(document.createElement('div'))
    const callback = vi.fn()

    useSwipeGesture(element, {
      onSwipeLeft: callback,
      threshold: 50
    })

    // Симулировать touchstart и touchmove с дельтой X > 50
    element.value!.dispatchEvent(new TouchEvent('touchstart', {
      touches: [{ clientX: 100, clientY: 100 } as Touch]
    }))

    element.value!.dispatchEvent(new TouchEvent('touchmove', {
      touches: [{ clientX: 40, clientY: 100 } as Touch]
    }))

    element.value!.dispatchEvent(new TouchEvent('touchend'))

    expect(callback).toHaveBeenCalled()
  })

  it('should ignore swipe below threshold', () => {
    const element = ref<HTMLElement>(document.createElement('div'))
    const callback = vi.fn()

    useSwipeGesture(element, {
      onSwipeLeft: callback,
      threshold: 50
    })

    // Дельта < threshold
    element.value!.dispatchEvent(new TouchEvent('touchstart', {
      touches: [{ clientX: 100, clientY: 100 } as Touch]
    }))

    element.value!.dispatchEvent(new TouchEvent('touchmove', {
      touches: [{ clientX: 90, clientY: 100 } as Touch]
    }))

    element.value!.dispatchEvent(new TouchEvent('touchend'))

    expect(callback).not.toHaveBeenCalled()
  })
})
```

---

## Производительность

### Оптимизации

1. **Ленивая отрисовка компонентов** — только активный режим отображается на экране (Week/Day/Meal)
2. **Virtual scroll** (опционально) — для Week view с большим числом дней можно добавить виртуальную прокрутку
3. **Computed с кешированием** — `sortedMeals` в MealCard кешируется и пересчитывается только при изменении `meals`
4. **requestAnimationFrame для свайпа** — useSwipeGesture использует RAF для плавных анимаций

### Сложность

- **Сортировка приёмов:** O(n log n) где n — количество приёмов в меню (обычно 7×3 = 21)
- **Свайп-обработка:** O(1) постоянное время для каждого жеста
- **Переход между режимами:** O(1)

---

## Совместимость

### Версия 0.9.1

Все изменения полностью совместимы с v0.9.1:

- Экран сводки блюд с сортировкой работает без изменений в API
- Мобильная навигация полностью заменяет старый snap-scroll (непрерывная миграция)
- Desktop view (PlannerGrid) не изменяется

### Вложенные рецепты (v0.6.0)

Три режима мобильной навигации поддерживают вложенные рецепты:

- GridCell в режиме Приём пищи показывает плоский список всех ингредиентов (с развёрнутыми вложенными рецептами)

### Штучный режим (v0.7.0)

Сортировка и мобильная навигация работают с штучным режимом без изменений.

---

## Будущие улучшения

1. **Свайп-индикаторы** — визуальные подсказки о возможности свайпа (стрелки по краям экрана)
2. **Анимация при жесте** — плавное перемещение контента во время свайпа (не только по окончанию)
3. **Кастомизация порога свайпа** — пользовательская настройка чувствительности
4. **Двойной тап** — быстрое добавление элемента в ячейку через двойной тап вместо одинарного
5. **Жест-пинч** — масштабирование сетки (приближение/отдаление)
6. **Предпоказ следующего дня/приёма** — частичное отображение рядом расположенного контента

---

**История версий:**

- **v0.10.0** (25.03.2026) — Сортировка приёмов пищи, трёхрежимная мобильная навигация (Неделя/День/Приём пищи) с жестовой навигацией
- **v0.9.1** (25.03.2026) — Kebab меню, скрытие купленных товаров, группировка по поставщику, сохранение last_login_at
- **v0.9.0** (24.03.2026) — Экран сводки блюд, экспорт плана приготовления
