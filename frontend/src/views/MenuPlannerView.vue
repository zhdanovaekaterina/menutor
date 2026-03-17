<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import type { MenuSlot } from '@/api/types'
import PlannerGrid from '@/components/planner/PlannerGrid.vue'
import SavedMenuList from '@/components/planner/SavedMenuList.vue'
import SourcePanel from '@/components/planner/SourcePanel.vue'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
import ExportModal from '@/components/ui/ExportModal.vue'
import ImportModal from '@/components/ui/ImportModal.vue'
import InputDialog from '@/components/ui/InputDialog.vue'
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

async function onSave() {
  if (!menuStore.current) {
    nameDialogOpen.value = true
    return
  }
  toast.show('Меню сохранено', 'success')
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
  <div class="h-full flex flex-col p-4 gap-4">
    <h1 class="text-xl font-bold">Планировщик меню</h1>

    <div class="flex-1 flex gap-4 min-h-0">
      <!-- Left: saved menus -->
      <div :class="leftPanelOpen ? 'w-48' : 'w-10'" class="shrink-0 transition-all duration-200 flex flex-col border-r bg-white overflow-hidden">
        <button
          class="p-2 text-gray-400 hover:text-gray-600 self-end shrink-0"
          :title="leftPanelOpen ? 'Свернуть' : 'Развернуть'"
          @click="leftPanelOpen = !leftPanelOpen"
        >
          <svg v-if="leftPanelOpen" class="w-4 h-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5 8.25 12l7.5-7.5" />
          </svg>
          <svg v-else class="w-4 h-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5" />
          </svg>
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

      <!-- Center: grid + actions -->
      <div class="flex-1 flex flex-col gap-4 min-w-0">
        <div class="flex-1 overflow-auto">
          <PlannerGrid
            :slots="slots"
            :recipe-names="recipeNames"
            :product-names="productNames"
            @add-item="onAddItem"
            @remove-item="onRemoveItem"
            @edit-item="onEditItem"
            @move-item="onMoveItem"
            @reorder-items="onReorderItems"
          />
        </div>
        <div class="flex items-center gap-3 pt-3 border-t flex-wrap">
          <!-- Primary actions -->
          <button
            class="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            :disabled="!menuStore.current"
            @click="onSave"
          >
            Сохранить
          </button>
          <button
            class="px-4 py-2 rounded-lg border border-gray-300 text-sm hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
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
              title="Импорт меню"
            >
              <!-- download arrow = import (bringing data in) -->
              <svg class="w-4 h-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12 12 16.5m0 0L7.5 12m4.5 4.5V3" />
              </svg>
            </button>
            <button
              class="p-2 rounded-lg border border-gray-300 text-sm hover:bg-gray-50 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              :disabled="!menuStore.current"
              @click="exportOpen = true"
              title="Экспорт меню"
            >
              <!-- upload arrow = export (sending data out) -->
              <svg class="w-4 h-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5m-13.5-9L12 3m0 0 4.5 4.5M12 3v13.5" />
              </svg>
            </button>
          </div>

          <div class="flex-1" />

          <!-- Call-to-action -->
          <button
            class="px-4 py-2 rounded-lg bg-green-600 text-white text-sm font-medium hover:bg-green-700 transition-colors"
            @click="onGenerateShoppingList"
          >
            Сформировать список покупок
          </button>
        </div>
      </div>

      <!-- Right: source panel -->
      <div :class="rightPanelOpen ? 'w-56' : 'w-10'" class="shrink-0 transition-all duration-200 flex flex-col border-l bg-white overflow-hidden">
        <button
          class="p-2 text-gray-400 hover:text-gray-600 self-start shrink-0"
          :title="rightPanelOpen ? 'Свернуть' : 'Развернуть'"
          @click="rightPanelOpen = !rightPanelOpen"
        >
          <svg v-if="rightPanelOpen" class="w-4 h-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5" />
          </svg>
          <svg v-else class="w-4 h-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5 8.25 12l7.5-7.5" />
          </svg>
        </button>
        <div v-show="rightPanelOpen" class="flex-1 min-h-0">
          <SourcePanel
            :recipes="recipeStore.items"
            :products="productStore.items"
            :family-members="familyStore.items"
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
      @confirm="onEditConfirm"
      @cancel="editSlot = null"
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
  </div>
</template>
