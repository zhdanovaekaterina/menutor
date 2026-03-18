<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import type { MenuSlot } from '@/api/types'
import MobileItemPicker from '@/components/planner/MobileItemPicker.vue'
import PlannerGrid from '@/components/planner/PlannerGrid.vue'
import SavedMenuList from '@/components/planner/SavedMenuList.vue'
import SourcePanel from '@/components/planner/SourcePanel.vue'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
import ExportModal from '@/components/ui/ExportModal.vue'
import ImportModal from '@/components/ui/ImportModal.vue'
import InputDialog from '@/components/ui/InputDialog.vue'
import IconCart from '@/components/ui/icons/IconCart.vue'
import IconChevronLeft from '@/components/ui/icons/IconChevronLeft.vue'
import IconChevronRight from '@/components/ui/icons/IconChevronRight.vue'
import IconClose from '@/components/ui/icons/IconClose.vue'
import IconDownload from '@/components/ui/icons/IconDownload.vue'
import IconHamburger from '@/components/ui/icons/IconHamburger.vue'
import IconUpload from '@/components/ui/icons/IconUpload.vue'
import { useFamilyStore } from '@/stores/family'
import { useMenuStore } from '@/stores/menus'
import { useProductStore } from '@/stores/products'
import { useRecipeStore } from '@/stores/recipes'
import { useShoppingListStore } from '@/stores/shoppingList'
import { useToastStore } from '@/stores/toast'

const router = useRouter()
const menuStore = useMenuStore()
const recipeStore = useRecipeStore()
const productStore = useProductStore()
const familyStore = useFamilyStore()
const shoppingStore = useShoppingListStore()
const toast = useToastStore()

const isXl = ref(typeof window !== 'undefined' && window.innerWidth >= 1280)
const leftPanelOpen = ref(true)
const rightPanelOpen = ref(isXl.value)

const mobileLeftOpen = ref(false)

const pickerOpen = ref(false)
const pickerDay = ref(0)
const pickerMealType = ref('')

const nameDialogOpen = ref(false)
const confirmDeleteOpen = ref(false)
const confirmClearOpen = ref(false)
const exportOpen = ref(false)
const importOpen = ref(false)
const editSlot = ref<MenuSlot | null>(null)
const editValue = ref('')

onMounted(async () => {
  await Promise.all([
    menuStore.load(),
    recipeStore.load(),
    productStore.load(),
    familyStore.load(),
  ])
})

const selectedId = computed(() => menuStore.current?.id ?? null)
const slots = computed(() => menuStore.current?.slots ?? [])
const pageTitle = computed(() => menuStore.current?.name ?? 'Планировщик меню')

const totalFamilyPortions = computed(() => {
  const sum = familyStore.items.reduce((acc, m) => acc + m.portion_multiplier, 0)
  return sum > 0 ? sum : 1
})

const recipeNames = computed(() =>
  Object.fromEntries(recipeStore.items.map((r) => [r.id, r.name])),
)
const productNames = computed(() =>
  Object.fromEntries(productStore.items.map((p) => [p.id, p.name])),
)

const dayLabels = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']

const pickerDayLabel = computed(() => dayLabels[pickerDay.value] ?? '')

const pickerExistingSlots = computed(() =>
  slots.value.filter(s => s.day === pickerDay.value && s.meal_type === pickerMealType.value)
)

async function onSelectMenu(id: number) {
  await menuStore.select(id)
}

async function onCreateMenu(name: string) {
  nameDialogOpen.value = false
  if (!name.trim()) return
  await menuStore.create(name.trim())
}

async function onDeleteMenu() {
  confirmDeleteOpen.value = false
  if (!selectedId.value) return
  await menuStore.remove(selectedId.value)
}

function onOpenPicker(day: number, mealType: string) {
  if (!menuStore.current) {
    toast.show('Сначала выберите меню', 'error')
    return
  }
  pickerDay.value = day
  pickerMealType.value = mealType
  pickerOpen.value = true
}

function onPickerSelect(data: { type: 'recipe' | 'product'; id: number }) {
  onAddItem(pickerDay.value, pickerMealType.value, data)
}

async function onAddItem(day: number, mealType: string, data: { type: 'recipe' | 'product'; id: number }) {
  if (!menuStore.current) { toast.show('Сначала выберите меню', 'error'); return }
  const slot: MenuSlot = {
    day,
    meal_type: mealType,
    recipe_id: data.type === 'recipe' ? data.id : null,
    product_id: data.type === 'product' ? data.id : null,
    quantity: data.type === 'product' ? 1 : null,
    unit: data.type === 'product' ? (productStore.items.find((p) => p.id === data.id)?.recipe_unit ?? null) : null,
    servings_override: data.type === 'recipe' ? totalFamilyPortions.value : null,
  }
  await menuStore.addSlotToMenu(slot)
}

async function onRemoveItem(day: number, mealType: string, data: { recipe_id?: number | null; product_id?: number | null }) {
  if (!menuStore.current) return
  await menuStore.removeSlotFromMenu({ day, meal_type: mealType, ...data })
}

function onEditItem(slot: MenuSlot) {
  editSlot.value = slot
  editValue.value = String(slot.servings_override ?? slot.quantity ?? 1)
}

async function onEditDelete() {
  const s = editSlot.value
  if (!s) return
  editSlot.value = null
  await onRemoveItem(s.day, s.meal_type, { recipe_id: s.recipe_id, product_id: s.product_id })
}

async function onEditConfirm(val: string) {
  const s = editSlot.value
  if (!s || !menuStore.current) return
  editSlot.value = null
  const num = parseFloat(val)
  if (isNaN(num) || num <= 0) return
  const updated: MenuSlot = {
    ...s,
    quantity: s.product_id != null ? num : s.quantity,
    servings_override: s.recipe_id != null ? num : s.servings_override,
  }
  await menuStore.addSlotToMenu(updated)
}

async function onMoveItem(slot: MenuSlot, toDay: number, toMealType: string, toIndex: number) {
  if (!menuStore.current) return
  try {
    await menuStore.moveSlot(slot, toDay, toMealType, toIndex)
  } catch (e: any) {
    toast.show(e?.response?.data?.detail ?? 'Ошибка перемещения', 'error')
  }
}

async function onReorderItems(day: number, mealType: string, orderedSlots: MenuSlot[]) {
  if (!menuStore.current) return
  try {
    await menuStore.reorderSlots(day, mealType, orderedSlots)
  } catch (e: any) {
    toast.show(e?.response?.data?.detail ?? 'Ошибка сортировки', 'error')
  }
}

async function onClear() {
  confirmClearOpen.value = false
  await menuStore.clear()
}

async function onGenerateShoppingList() {
  if (!menuStore.current) { toast.show('Сначала выберите меню', 'error'); return }
  await shoppingStore.generate(menuStore.current.id)
  router.push('/shopping-list')
}
</script>

<template>
  <div class="h-full flex flex-col p-3 sm:p-4 lg:p-6 gap-3 sm:gap-4">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-2">
        <!-- Mobile: hamburger to open left drawer (SavedMenuList) -->
        <button
          class="lg:hidden p-2 -ml-2 rounded-lg hover:bg-gray-100"
          @click="mobileLeftOpen = true"
        >
          <IconHamburger class="w-5 h-5" />
        </button>
        <h1 class="text-lg sm:text-xl font-bold lg:hidden">{{ pageTitle }}</h1>
        <h1 class="text-lg sm:text-xl font-bold hidden lg:block">Планировщик меню</h1>
      </div>
    </div>

    <div class="flex-1 flex gap-4 min-h-0">
      <!-- Left panel: hidden on mobile, collapsible on desktop -->
      <div :class="leftPanelOpen ? 'w-48' : 'w-10'" class="shrink-0 transition-all duration-200 flex flex-col bg-white overflow-hidden hidden lg:flex">
        <button
          class="p-2 text-gray-400 hover:text-gray-600 self-end shrink-0"
          :title="leftPanelOpen ? 'Свернуть' : 'Развернуть'"
          @click="leftPanelOpen = !leftPanelOpen"
        >
          <IconChevronLeft v-if="leftPanelOpen" class="w-4 h-4" />
          <IconChevronRight v-else class="w-4 h-4" />
        </button>
        <div v-show="leftPanelOpen" class="flex-1 min-h-0">
          <SavedMenuList
            :menus="menuStore.menus"
            :selected-id="selectedId"
            @select="onSelectMenu"
            @create="nameDialogOpen = true"
            @remove="confirmDeleteOpen = true"
          />
        </div>
      </div>

      <!-- Center: always visible -->
      <div class="flex-1 flex flex-col gap-4 min-w-0">
        <div class="flex-1 overflow-hidden lg:overflow-auto">
          <PlannerGrid
            :slots="slots"
            :recipe-names="recipeNames"
            :product-names="productNames"
            :picker-day="pickerOpen ? pickerDay : null"
            :picker-meal-type="pickerOpen ? pickerMealType : null"
            @add-item="onAddItem"
            @remove-item="onRemoveItem"
            @edit-item="onEditItem"
            @move-item="onMoveItem"
            @reorder-items="onReorderItems"
            @open-picker="onOpenPicker"
            @day-scrolled="pickerOpen = false"
          />
        </div>
        <div class="flex items-center gap-3 pt-3 border-t flex-wrap">
          <button
            class="px-3 py-2 rounded-lg border border-gray-300 text-sm hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            :disabled="!menuStore.current"
            @click="confirmClearOpen = true"
          >
            Очистить
          </button>

          <!-- Vertical divider -->
          <div class="w-px h-6 bg-gray-300" />

          <!-- Secondary actions: Import/Export as icon-only buttons -->
          <div class="flex items-center gap-1.5">
            <button
              class="p-2 rounded-lg border border-gray-300 text-sm hover:bg-gray-50 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              :disabled="!menuStore.current"
              @click="importOpen = true"
              title="Импорт"
            >
              <IconUpload class="w-4 h-4" />
            </button>
            <button
              class="p-2 rounded-lg border border-gray-300 text-sm hover:bg-gray-50 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              :disabled="!menuStore.current"
              @click="exportOpen = true"
              title="Экспорт"
            >
              <IconDownload class="w-4 h-4" />
            </button>
          </div>

          <div class="flex-1" />

          <!-- Call-to-action -->
          <button
            class="px-3 py-2 rounded-lg bg-green-600 text-white text-sm font-medium hover:bg-green-700 transition-colors flex-shrink-0"
            @click="onGenerateShoppingList"
          >
            <span class="hidden sm:inline">Сформировать список покупок</span>
            <span class="sm:hidden flex items-center gap-1">
              <IconCart class="w-4 h-4" />
              Список
            </span>
          </button>
        </div>
      </div>

      <!-- Right panel: hidden on mobile, collapsible on desktop -->
      <div :class="rightPanelOpen ? 'w-56' : 'w-10'" class="shrink-0 transition-all duration-200 flex flex-col bg-white overflow-hidden hidden lg:flex">
        <button
          class="p-2 text-gray-400 hover:text-gray-600 self-start shrink-0"
          :title="rightPanelOpen ? 'Свернуть' : 'Развернуть'"
          @click="rightPanelOpen = !rightPanelOpen"
        >
          <IconChevronRight v-if="rightPanelOpen" class="w-4 h-4" />
          <IconChevronLeft v-else class="w-4 h-4" />
        </button>
        <div v-show="rightPanelOpen" class="flex-1 min-h-0">
          <SourcePanel
            :recipes="recipeStore.items"
            :products="productStore.items"
            :family-members="familyStore.items"
            :recipe-categories="recipeStore.categories"
            :product-categories="productStore.categories"
          />
        </div>
      </div>
    </div>

    <InputDialog
      :open="nameDialogOpen"
      title="Новое меню"
      label="Название меню"
      @confirm="onCreateMenu"
      @cancel="nameDialogOpen = false"
    />
    <ConfirmDialog
      :open="confirmDeleteOpen"
      message="Удалить выбранное меню?"
      danger
      @confirm="onDeleteMenu"
      @cancel="confirmDeleteOpen = false"
    />
    <ConfirmDialog
      :open="confirmClearOpen"
      message="Очистить все слоты в меню?"
      @confirm="onClear"
      @cancel="confirmClearOpen = false"
    />
    <InputDialog
      :open="!!editSlot"
      :title="editSlot?.recipe_id != null ? 'Порции' : 'Количество'"
      :label="editSlot?.recipe_id != null ? 'Количество порций' : 'Количество'"
      :initial-value="editValue"
      input-type="number"
      :show-delete="true"
      @confirm="onEditConfirm"
      @cancel="editSlot = null"
      @delete="onEditDelete"
    />

    <ExportModal
      :open="exportOpen"
      entity-type="menus"
      :formats="[{ value: 'json', label: 'JSON' }]"
      :selected-ids="menuStore.current ? [menuStore.current.id] : []"
      @close="exportOpen = false"
    />
    <ImportModal
      :open="importOpen"
      entity-type="menus"
      :allowed-extensions="['json']"
      @close="importOpen = false"
      @imported="menuStore.load()"
    />

    <MobileItemPicker
      :open="pickerOpen"
      :day="pickerDay"
      :meal-type="pickerMealType"
      :day-label="pickerDayLabel"
      :recipes="recipeStore.items"
      :products="productStore.items"
      :existing-slots="pickerExistingSlots"
      :recipe-categories="recipeStore.categories"
      :product-categories="productStore.categories"
      @close="pickerOpen = false"
      @select="onPickerSelect"
    />

    <!-- Mobile: Left drawer (SavedMenuList) -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="mobileLeftOpen" class="lg:hidden fixed inset-0 bg-black/40 z-40" @click="mobileLeftOpen = false" />
      </Transition>
      <Transition name="slide-left">
        <div v-if="mobileLeftOpen" class="lg:hidden fixed inset-y-0 left-0 w-72 bg-white z-50 shadow-xl flex flex-col p-4">
          <div class="flex items-center justify-between mb-3">
            <h2 class="font-semibold">Меню</h2>
            <button class="p-1 rounded hover:bg-gray-100" @click="mobileLeftOpen = false">
              <IconClose class="w-5 h-5" />
            </button>
          </div>
          <SavedMenuList
            :menus="menuStore.menus"
            :selected-id="selectedId"
            @select="(id) => { onSelectMenu(id); mobileLeftOpen = false }"
            @create="nameDialogOpen = true; mobileLeftOpen = false"
            @remove="confirmDeleteOpen = true; mobileLeftOpen = false"
          />
        </div>
      </Transition>
    </Teleport>

  </div>
</template>

<style scoped>
.slide-left-enter-active, .slide-left-leave-active {
  transition: transform 0.25s ease;
}
.slide-left-enter-from, .slide-left-leave-to {
  transform: translateX(-100%);
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>
