<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import type { MenuSlot } from '@/api/types'
import PlannerGrid from '@/components/planner/PlannerGrid.vue'
import SavedMenuList from '@/components/planner/SavedMenuList.vue'
import SourcePanel from '@/components/planner/SourcePanel.vue'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
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

const nameDialogOpen = ref(false)
const confirmDeleteOpen = ref(false)
const confirmClearOpen = ref(false)
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

const recipeNames = computed(() =>
  Object.fromEntries(recipeStore.recipes.map((r) => [r.id, r.name])),
)
const productNames = computed(() =>
  Object.fromEntries(productStore.products.map((p) => [p.id, p.name])),
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
    unit: data.type === 'product' ? (productStore.products.find((p) => p.id === data.id)?.recipe_unit ?? null) : null,
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
      <div class="w-48 shrink-0">
        <SavedMenuList
          :menus="menuStore.menus"
          :selected-id="selectedId"
          @select="onSelectMenu"
          @create="nameDialogOpen = true"
          @remove="confirmDeleteOpen = true"
        />
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
          />
        </div>
        <div class="flex items-center gap-3 pt-2 border-t">
          <button class="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm hover:bg-blue-700" @click="onSave">
            Сохранить
          </button>
          <button class="px-4 py-2 rounded-lg border border-gray-300 text-sm hover:bg-gray-50"
            @click="confirmClearOpen = true">
            Очистить
          </button>
          <div class="flex-1" />
          <button class="px-4 py-2 rounded-lg bg-green-600 text-white text-sm hover:bg-green-700"
            @click="onGenerateShoppingList">
            Сформировать список покупок
          </button>
        </div>
      </div>

      <!-- Right: source panel -->
      <div class="w-56 shrink-0">
        <SourcePanel
          :recipes="recipeStore.recipes"
          :products="productStore.products"
          :family-members="familyStore.members"
        />
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
  </div>
</template>
