<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import type { MenuSlot } from '@/api/types'
import MobileItemPicker from '@/components/planner/MobileItemPicker.vue'
import PlannerGrid from '@/components/planner/PlannerGrid.vue'
import SavedMenuList from '@/components/planner/SavedMenuList.vue'
import SourcePanel from '@/components/planner/SourcePanel.vue'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
import ContextMenu from '@/components/ui/ContextMenu.vue'
import ExportModal from '@/components/ui/ExportModal.vue'
import ImportModal from '@/components/ui/ImportModal.vue'
import InputDialog from '@/components/ui/InputDialog.vue'
import SlotEditDialog from '@/components/ui/SlotEditDialog.vue'
import SplitDropdownButton from '@/components/ui/SplitDropdownButton.vue'
import IconCart from '@/components/ui/icons/IconCart.vue'
import IconChevronLeft from '@/components/ui/icons/IconChevronLeft.vue'
import IconChevronRight from '@/components/ui/icons/IconChevronRight.vue'
import IconClose from '@/components/ui/icons/IconClose.vue'
import IconDownload from '@/components/ui/icons/IconDownload.vue'
import IconHamburger from '@/components/ui/icons/IconHamburger.vue'
import IconUpload from '@/components/ui/icons/IconUpload.vue'
import { exportEntities, exportMenuPdf } from '@/api/client'
import { useContextMenu } from '@/composables/useContextMenu'
import { formatUnit } from '@/utils/units'
import { downloadBlob } from '@/composables/useFileDownload'
import { useCategoryStore } from '@/stores/categories'
import { useFamilyStore } from '@/stores/family'
import { useMenuStore } from '@/stores/menus'
import { useProductStore } from '@/stores/products'
import { useRecipeStore } from '@/stores/recipes'
import { useShoppingListStore } from '@/stores/shoppingList'
import { useToastStore } from '@/stores/toast'

const router = useRouter()
const { state: contextMenuState } = useContextMenu()
const menuStore = useMenuStore()
const recipeStore = useRecipeStore()
const productStore = useProductStore()
const familyStore = useFamilyStore()
const categoryStore = useCategoryStore()
const shoppingStore = useShoppingListStore()
const toast = useToastStore()

const isXl = ref(typeof window !== 'undefined' && window.innerWidth >= 1280)
const leftPanelOpen = ref(true)
const rightPanelOpen = ref(false)
const autoSwitchDone = ref(false)

function doAutoSwitch() {
  if (autoSwitchDone.value) return
  autoSwitchDone.value = true
  leftPanelOpen.value = false
  rightPanelOpen.value = true
}

const mobileLeftOpen = ref(false)
const mobileMenuOpen = ref(false)

const pickerOpen = ref(false)
const pickerDay = ref(0)
const pickerMealType = ref('')

const nameDialogOpen = ref(false)
const confirmDeleteOpen = ref(false)
const confirmClearOpen = ref(false)
const exportOpen = ref(false)
const importOpen = ref(false)
const mobilePdfOpen = ref(false)
const editSlot = ref<MenuSlot | null>(null)
const editValue = ref('')
const editPiecesMode = ref(false)
const editPortions = ref('')
const editPieces = ref('')
const editCalculatedPieces = ref(0)

onMounted(async () => {
  const previousId = menuStore.selectedId
  await Promise.all([
    menuStore.load(),
    recipeStore.load(),
    productStore.load(),
    familyStore.load(),
    categoryStore.load('product'),
    categoryStore.load('recipe'),
  ])
  if (previousId !== null) {
    await menuStore.select(previousId)
  }
})

const selectedId = computed(() => menuStore.current?.id ?? null)
const slots = computed(() => menuStore.current?.slots ?? [])
const pageTitle = computed(() => menuStore.current?.name ?? 'Планировщик меню')

const totalFamilyPortions = computed(() => {
  const sum = familyStore.items.reduce((acc, m) => acc + m.portion_multiplier, 0)
  return sum > 0 ? sum : 1
})

const recipeNames = computed(() =>
  Object.fromEntries(recipeStore.allItems.map((r) => [r.id, r.name])),
)
const productNames = computed(() =>
  Object.fromEntries(productStore.allItems.map((p) => [p.id, p.name])),
)

const dayLabels = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']

const pickerDayLabel = computed(() => dayLabels[pickerDay.value] ?? '')

const pickerExistingSlots = computed(() =>
  slots.value.filter(s => s.day === pickerDay.value && s.meal_type === pickerMealType.value)
)

async function onSelectMenu(id: number) {
  await menuStore.select(id)
  doAutoSwitch()
}

async function onCreateMenu(name: string) {
  nameDialogOpen.value = false
  if (!name.trim()) return
  await menuStore.create(name.trim())
  doAutoSwitch()
}

async function onDeleteMenu() {
  confirmDeleteOpen.value = false
  if (!selectedId.value) return
  await menuStore.remove(selectedId.value)
}

async function onOpenPicker(day: number, mealType: string) {
  await menuStore.ensureMenuSelected()
  pickerDay.value = day
  pickerMealType.value = mealType
  pickerOpen.value = true
}

function onPickerSelect(data: { type: 'recipe' | 'product'; id: number }) {
  onAddItem(pickerDay.value, pickerMealType.value, data)
}

function onPickerRemove(data: { type: 'recipe' | 'product'; id: number }) {
  onRemoveItem(pickerDay.value, pickerMealType.value, {
    recipe_id: data.type === 'recipe' ? data.id : null,
    product_id: data.type === 'product' ? data.id : null,
  })
}

async function onAddItem(day: number, mealType: string, data: { type: 'recipe' | 'product'; id: number }) {
  await menuStore.ensureMenuSelected()
  const slot: MenuSlot = {
    day,
    meal_type: mealType,
    recipe_id: data.type === 'recipe' ? data.id : null,
    product_id: data.type === 'product' ? data.id : null,
    unit: data.type === 'product' ? (productStore.allItems.find((p) => p.id === data.id)?.recipe_unit ?? null) : null,
    quantity: data.type === 'product' ? (productStore.allItems.find((p) => p.id === data.id)?.recipe_unit === 'g' ? 100 : 1) : null,
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

  if (slot.recipe_id != null) {
    const recipe = recipeStore.allItems.find(r => r.id === slot.recipe_id)
    if (recipe?.total_pieces != null && recipe?.pieces_per_portion != null) {
      editPiecesMode.value = true
      const portions = slot.servings_override ?? totalFamilyPortions.value
      editPortions.value = String(portions)
      const calculated = Math.max(1, Math.round(portions * recipe.pieces_per_portion))
      editCalculatedPieces.value = calculated
      editPieces.value = String(slot.pieces_override ?? calculated)
      return
    }
  }

  editPiecesMode.value = false
  editValue.value = String(slot.servings_override ?? slot.quantity ?? 1)
}

async function onEditDelete() {
  const s = editSlot.value
  if (!s) return
  editSlot.value = null
  editPiecesMode.value = false
  await onRemoveItem(s.day, s.meal_type, { recipe_id: s.recipe_id, product_id: s.product_id })
}

async function onEditConfirm(val: string) {
  const s = editSlot.value
  if (!s || !menuStore.current) return
  editSlot.value = null

  if (editPiecesMode.value) {
    const pcs = parseInt(editPieces.value)
    if (isNaN(pcs) || pcs < 1) return
    const updated: MenuSlot = {
      ...s,
      pieces_override: pcs !== editCalculatedPieces.value ? pcs : null,
    }
    await menuStore.addSlotToMenu(updated)
    return
  }

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

async function onCopyMenu() {
  if (!selectedId.value) return
  await menuStore.copy(selectedId.value)
}

const exportFormat = ref<'pdf' | 'json'>('pdf')
const paperSize = ref<'a4' | 'a3'>('a4')
const exportLoading = ref(false)

const exportFormats = [
  { value: 'pdf', label: 'PDF' },
  { value: 'json', label: 'JSON' },
]

async function onExportMenu() {
  if (!menuStore.current) return
  exportLoading.value = true
  try {
    if (exportFormat.value === 'pdf') {
      const blob = await exportMenuPdf(menuStore.current.id, paperSize.value)
      downloadBlob(blob, `menu_${menuStore.current.name}.pdf`)
    } else {
      const blob = await exportEntities('menus', 'json', [menuStore.current.id])
      downloadBlob(blob, `menu_${menuStore.current.name}.json`)
    }
  } catch (e: any) {
    let message = 'Ошибка экспорта меню'
    const data = e?.response?.data
    if (data instanceof Blob) {
      try {
        const text = await data.text()
        const parsed = JSON.parse(text)
        if (parsed?.detail) message = parsed.detail
      } catch {
        // keep default message
      }
    } else if (data?.detail) {
      message = data.detail
    }
    toast.show(message, 'error')
  } finally {
    exportLoading.value = false
  }
}

async function onGenerateShoppingList() {
  if (!menuStore.current) { toast.show('Сначала выберите меню', 'error'); return }
  await shoppingStore.generate(menuStore.current.id)
  router.push({ path: '/shopping-list', query: { from: 'planner' } })
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

      <!-- Mobile: kebab menu (right side of header) -->
      <div class="lg:hidden relative">
        <button
          class="p-2 rounded-lg hover:bg-gray-100 text-gray-600"
          @click="mobileMenuOpen = !mobileMenuOpen"
          aria-label="Действия"
        >
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 6.75a.75.75 0 1 1 0-1.5.75.75 0 0 1 0 1.5ZM12 12.75a.75.75 0 1 1 0-1.5.75.75 0 0 1 0 1.5ZM12 18.75a.75.75 0 1 1 0-1.5.75.75 0 0 1 0 1.5Z" />
          </svg>
        </button>
        <div v-if="mobileMenuOpen" class="fixed inset-0 z-40" @click="mobileMenuOpen = false" />
        <div v-if="mobileMenuOpen" class="absolute right-0 top-full mt-1 bg-white border rounded-xl shadow-xl z-50 min-w-[220px] py-1 overflow-hidden">
          <button
            class="w-full text-left px-4 py-3 text-sm hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
            :disabled="!menuStore.current"
            @click="router.push(`/menus/${menuStore.current?.id}/summary`); mobileMenuOpen = false"
          >Обзор блюд</button>
          <button
            class="w-full text-left px-4 py-3 text-sm hover:bg-gray-50 font-medium text-green-700"
            @click="onGenerateShoppingList(); mobileMenuOpen = false"
          >Сформировать список покупок</button>
          <div class="border-t mx-3 my-1" />
          <button
            class="w-full text-left px-4 py-3 text-sm hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
            :disabled="!menuStore.current"
            @click="confirmClearOpen = true; mobileMenuOpen = false"
          >Очистить меню</button>
          <button
            class="w-full text-left px-4 py-3 text-sm hover:bg-gray-50"
            @click="importOpen = true; mobileMenuOpen = false"
          >Импорт</button>
          <button
            class="w-full text-left px-4 py-3 text-sm hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
            :disabled="!menuStore.current"
            @click="exportOpen = true; mobileMenuOpen = false"
          >Экспорт (JSON)</button>
          <button
            class="w-full text-left px-4 py-3 text-sm hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
            :disabled="!menuStore.current"
            @click="mobilePdfOpen = true; mobileMenuOpen = false"
          >Экспорт PDF</button>
        </div>
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
            :menus="menuStore.sortedMenus"
            :selected-id="selectedId"
            @select="onSelectMenu"
            @create="nameDialogOpen = true"
            @copy="onCopyMenu"
            @remove="confirmDeleteOpen = true"
          />
        </div>
      </div>

      <!-- Center: always visible -->
      <div class="flex-1 flex flex-col gap-4 min-w-0">
        <div class="flex-1 overflow-hidden lg:overflow-x-auto">
          <PlannerGrid
            :slots="slots"
            :recipe-names="recipeNames"
            :product-names="productNames"
            :picker-day="pickerOpen ? pickerDay : null"
            :picker-meal-type="pickerOpen ? pickerMealType : null"
            :menu-id="selectedId"
            @add-item="onAddItem"
            @remove-item="onRemoveItem"
            @edit-item="onEditItem"
            @move-item="onMoveItem"
            @reorder-items="onReorderItems"
            @open-picker="onOpenPicker"
            @day-scrolled="pickerOpen = false"
          />
        </div>
        <div class="hidden lg:flex items-center gap-3 pt-3 border-t flex-wrap">
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
              title="Экспорт (выбор формата)"
            >
              <IconDownload class="w-4 h-4" />
            </button>
            <div class="flex items-center gap-2">
              <SplitDropdownButton
                :formats="exportFormats"
                v-model="exportFormat"
                :loading="exportLoading"
                :disabled="!menuStore.current"
                @export="onExportMenu"
              />
              <div
                v-if="exportFormat === 'pdf'"
                class="flex items-center rounded-lg border border-gray-300 text-sm"
              >
                <button
                  type="button"
                  class="px-2.5 py-2 transition-colors rounded-l-lg"
                  :class="paperSize === 'a4' ? 'bg-blue-600 text-white' : 'hover:bg-gray-50 text-gray-700'"
                  @click="paperSize = 'a4'"
                >
                  A4
                </button>
                <button
                  type="button"
                  class="px-2.5 py-2 transition-colors border-l border-gray-300 rounded-r-lg"
                  :class="paperSize === 'a3' ? 'bg-blue-600 text-white' : 'hover:bg-gray-50 text-gray-700'"
                  @click="paperSize = 'a3'"
                >
                  A3
                </button>
              </div>
            </div>
          </div>

          <div class="flex-1" />

          <!-- Meal Summary button -->
          <button
            class="px-3 py-2 rounded-lg border border-blue-200 bg-blue-50 text-blue-700 text-sm font-medium hover:bg-blue-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex-shrink-0"
            :disabled="!menuStore.current"
            @click="router.push(`/menus/${menuStore.current?.id}/summary`)"
          >
            <span class="hidden sm:inline">Обзор блюд</span>
            <span class="sm:hidden">Обзор</span>
          </button>

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
            :recipes="recipeStore.allItems"
            :products="productStore.allItems"
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
    <!-- Edit dialog: standard (non-pieces) -->
    <InputDialog
      :open="!!editSlot && !editPiecesMode"
      :title="editSlot?.recipe_id != null ? 'Порции' : 'Количество'"
      :label="editSlot?.recipe_id != null ? 'Количество порций' : (editSlot?.unit ? `Количество, ${formatUnit(editSlot.unit)}` : 'Количество')"
      :initial-value="editValue"
      input-type="number"
      :show-delete="true"
      @confirm="onEditConfirm"
      @cancel="editSlot = null"
      @delete="onEditDelete"
    />

    <!-- Edit dialog: pieces mode -->
    <SlotEditDialog
      :open="!!editSlot && editPiecesMode"
      :recipe-name="editSlot?.recipe_id != null ? (recipeNames[editSlot.recipe_id] ?? '') : ''"
      :portions="editPortions"
      :calculated-pieces="editCalculatedPieces"
      v-model:pieces="editPieces"
      :show-delete="true"
      @confirm="onEditConfirm('')"
      @cancel="editSlot = null; editPiecesMode = false"
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
      :recipes="recipeStore.allItems"
      :products="productStore.allItems"
      :existing-slots="pickerExistingSlots"
      :recipe-categories="recipeStore.categories"
      :product-categories="productStore.categories"
      @close="pickerOpen = false"
      @select="onPickerSelect"
      @remove="onPickerRemove"
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
            :menus="menuStore.sortedMenus"
            :selected-id="selectedId"
            @select="(id) => { onSelectMenu(id); mobileLeftOpen = false }"
            @create="nameDialogOpen = true; mobileLeftOpen = false"
            @copy="onCopyMenu"
            @remove="confirmDeleteOpen = true; mobileLeftOpen = false"
          />
        </div>
      </Transition>
    </Teleport>

    <Teleport to="body">
      <ContextMenu
        v-if="contextMenuState.visible"
        :items="contextMenuState.items"
        :x="contextMenuState.x"
        :y="contextMenuState.y"
      />
    </Teleport>

    <!-- Mobile PDF export modal (paper size picker) -->
    <Teleport to="body">
      <div v-if="mobilePdfOpen" class="fixed inset-0 bg-black/50 flex items-end sm:items-center justify-center z-50">
        <div class="bg-white rounded-t-2xl sm:rounded-xl shadow-xl max-w-sm w-full sm:mx-4 p-6">
          <h3 class="text-lg font-semibold mb-4">Экспорт PDF</h3>
          <p class="text-sm text-gray-600 mb-4">Выберите формат бумаги:</p>
          <div class="flex gap-3 mb-6">
            <button
              type="button"
              class="flex-1 py-3 rounded-lg border-2 text-sm font-medium transition-colors"
              :class="paperSize === 'a4' ? 'border-blue-600 bg-blue-50 text-blue-700' : 'border-gray-300 text-gray-700 hover:bg-gray-50'"
              @click="paperSize = 'a4'"
            >A4</button>
            <button
              type="button"
              class="flex-1 py-3 rounded-lg border-2 text-sm font-medium transition-colors"
              :class="paperSize === 'a3' ? 'border-blue-600 bg-blue-50 text-blue-700' : 'border-gray-300 text-gray-700 hover:bg-gray-50'"
              @click="paperSize = 'a3'"
            >A3</button>
          </div>
          <div class="flex gap-3">
            <button
              class="flex-1 py-2 rounded-lg border border-gray-300 text-sm hover:bg-gray-50 transition-colors"
              @click="mobilePdfOpen = false"
            >Отмена</button>
            <button
              class="flex-1 py-2 rounded-lg bg-blue-600 text-white text-sm hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              :disabled="exportLoading"
              @click="exportFormat = 'pdf'; onExportMenu(); mobilePdfOpen = false"
            >{{ exportLoading ? 'Загрузка…' : 'Скачать' }}</button>
          </div>
        </div>
      </div>
    </Teleport>

  </div>
</template>

