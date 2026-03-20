<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import Sortable from 'sortablejs'
import type { MenuSlot } from '@/api/types'
import { useContextMenu } from '@/composables/useContextMenu'
import { usePlannerClipboard } from '@/composables/usePlannerClipboard'
import { useMenuStore } from '@/stores/menus'
import { useRecipeStore } from '@/stores/recipes'
import ItemRow from './ItemRow.vue'
import IconPlus from '@/components/ui/icons/IconPlus.vue'

const props = defineProps<{
  day: number
  mealType: string
  slots: MenuSlot[]
  recipeNames: Record<number, string>
  productNames: Record<number, string>
  pickerActive?: boolean
}>()

const emit = defineEmits<{
  addItem: [data: { type: 'recipe' | 'product'; id: number }]
  removeItem: [data: { recipe_id?: number | null; product_id?: number | null }]
  editItem: [slot: MenuSlot]
  moveItem: [slot: MenuSlot, toDay: number, toMealType: string, toIndex: number]
  reorderItems: [day: number, mealType: string, orderedSlots: MenuSlot[]]
  openPicker: []
}>()

const dragOver = ref(false)
const listRef = ref<HTMLElement>()

const recipeStore = useRecipeStore()

// Context menu
const { open: openContextMenu, close: closeContextMenu } = useContextMenu()
const { hasClipboard, copySlot, pasteSlot } = usePlannerClipboard()
const menuStore = useMenuStore()

function buildContextMenuItems() {
  return [
    {
      label: 'Копировать',
      action: () => {
        copySlot(cellSlots.value)
        closeContextMenu()
      },
    },
    {
      label: 'Вставить',
      disabled: !hasClipboard.value,
      action: async () => {
        const items = pasteSlot()
        if (!items || items.length === 0) return
        await menuStore.ensureMenuSelected()
        await menuStore.mergeItemsIntoSlot(props.day, props.mealType, items)
        closeContextMenu()
      },
    },
  ]
}

function onContextMenu(e: MouseEvent) {
  openContextMenu(e.clientX, e.clientY, buildContextMenuItems())
}

// Long-press for mobile context menu
let longPressTimer: ReturnType<typeof setTimeout> | null = null
let touchMoved = false

function onTouchStart(e: TouchEvent) {
  touchMoved = false
  const touch = e.touches[0]
  if (!touch) return
  longPressTimer = setTimeout(() => {
    if (!touchMoved) {
      openContextMenu(touch.clientX, touch.clientY, buildContextMenuItems())
    }
  }, 500)
}

function onTouchMove() {
  touchMoved = true
  if (longPressTimer !== null) {
    clearTimeout(longPressTimer)
    longPressTimer = null
  }
}

function onTouchEnd() {
  if (longPressTimer !== null) {
    clearTimeout(longPressTimer)
    longPressTimer = null
  }
}

let sortable: Sortable | null = null

const cellSlots = computed(() =>
  props.slots
    .filter((s) => s.day === props.day && s.meal_type === props.mealType)
    .sort((a, b) => (a.position ?? 0) - (b.position ?? 0)),
)

function itemName(slot: MenuSlot) {
  if (slot.recipe_id != null) return props.recipeNames[slot.recipe_id] ?? `#${slot.recipe_id}`
  if (slot.product_id != null) return props.productNames[slot.product_id] ?? `#${slot.product_id}`
  return '?'
}

function formatNumber(n: number): string {
  return n % 1 === 0 ? String(n) : n.toFixed(1)
}

function itemDetail(slot: MenuSlot) {
  if (slot.recipe_id != null) {
    const s = slot.servings_override ?? slot.quantity
    const recipe = recipeStore.items.find(r => r.id === slot.recipe_id)

    if (recipe?.total_pieces != null && recipe?.pieces_per_portion != null) {
      const portions = s != null ? formatNumber(s) : '?'
      const pcs = slot.pieces_override
        ?? Math.max(1, Math.round((s ?? 1) * recipe.pieces_per_portion))
      return { text: '', piecesDetail: { portions, pieces: pcs } }
    }

    return { text: s != null ? `${formatNumber(s)} п.` : '', piecesDetail: null }
  }
  if (slot.product_id != null && slot.quantity != null) {
    return { text: `${slot.quantity} ${slot.unit ?? ''}`, piecesDetail: null }
  }
  return { text: '', piecesDetail: null }
}

/* Native drop from SourcePanel (not SortableJS) */
function onDragOver(e: DragEvent) {
  if (e.dataTransfer?.types.includes('application/json')) {
    e.preventDefault()
    dragOver.value = true
  }
}

function onDrop(e: DragEvent) {
  dragOver.value = false
  const raw = e.dataTransfer?.getData('application/json')
  if (!raw) return
  e.preventDefault()
  try {
    const data = JSON.parse(raw)
    if (data.type && data.id) {
      emit('addItem', data as { type: 'recipe' | 'product'; id: number })
    }
  } catch { /* ignore */ }
}

function initSortable() {
  if (!listRef.value) return
  sortable = Sortable.create(listRef.value, {
    group: 'menu-slots',
    animation: 150,
    ghostClass: 'sortable-ghost',
    dragClass: 'sortable-drag',
    onEnd(evt) {
      const fromDay = Number(evt.from.dataset.day)
      const fromMeal = evt.from.dataset.mealType!
      const toDay = Number(evt.to.dataset.day)
      const toMeal = evt.to.dataset.mealType!
      const oldIdx = evt.oldIndex!
      const newIdx = evt.newIndex!

      /* Undo SortableJS DOM changes — let Vue re-render */
      if (evt.from !== evt.to) {
        evt.to.removeChild(evt.item)
        const ref = evt.from.children[oldIdx]
        if (ref) evt.from.insertBefore(evt.item, ref)
        else evt.from.appendChild(evt.item)
      } else if (oldIdx !== newIdx) {
        evt.from.removeChild(evt.item)
        const ref = evt.from.children[oldIdx]
        if (ref) evt.from.insertBefore(evt.item, ref)
        else evt.from.appendChild(evt.item)
      }

      /* Resolve source slot from the index within that cell */
      const sourceSlots = props.slots
        .filter((s) => s.day === fromDay && s.meal_type === fromMeal)
        .sort((a, b) => (a.position ?? 0) - (b.position ?? 0))
      const movedSlot = sourceSlots[oldIdx]
      if (!movedSlot) return

      if (fromDay !== toDay || fromMeal !== toMeal) {
        emit('moveItem', movedSlot, toDay, toMeal, newIdx)
      } else if (oldIdx !== newIdx) {
        const reordered = [...sourceSlots]
        reordered.splice(oldIdx, 1)
        reordered.splice(newIdx, 0, movedSlot)
        emit('reorderItems', fromDay, fromMeal, reordered)
      }
    },
  })
}

onMounted(initSortable)
onUnmounted(() => sortable?.destroy())

watch(
  () => cellSlots.value.length,
  () => {
    sortable?.destroy()
    initSortable()
  },
)
</script>

<template>
  <div
    :class="[
      dragOver ? 'ring-2 ring-blue-300 bg-blue-50/50' : '',
      pickerActive ? 'ring-2 ring-blue-400 ring-offset-1 bg-blue-50/60' : '',
      !dragOver && !pickerActive ? 'bg-white' : ''
    ]"
    class="relative h-full min-h-[100px] p-1 flex flex-col gap-1"
    @contextmenu.prevent="onContextMenu"
    @touchstart.passive="onTouchStart"
    @touchmove.passive="onTouchMove"
    @touchend.passive="onTouchEnd"
    @dragover="onDragOver"
    @dragleave="dragOver = false"
    @drop="onDrop"
  >
    <div ref="listRef" :data-day="day" :data-meal-type="mealType" class="flex flex-col gap-1 min-h-[8px] flex-1 max-h-40 overflow-y-auto">
      <ItemRow
        v-for="(slot, i) in cellSlots"
        :key="`${slot.recipe_id ?? ''}-${slot.product_id ?? ''}`"
        :name="itemName(slot)"
        :detail="itemDetail(slot).text"
        :pieces-detail="itemDetail(slot).piecesDetail"
        :variant="slot.recipe_id != null ? 'recipe' : 'product'"
        @remove="emit('removeItem', { recipe_id: slot.recipe_id, product_id: slot.product_id })"
        @click="emit('editItem', slot)"
      />
    </div>
    <!-- Mobile add button -->
    <button
      class="lg:hidden absolute bottom-1.5 right-1.5 w-9 h-9 flex items-center justify-center rounded-full bg-blue-500 text-white shadow-md active:bg-blue-600 transition-colors"
      aria-label="Добавить"
      @click.stop="emit('openPicker')"
    >
      <IconPlus class="w-5 h-5" />
    </button>
  </div>
</template>

<style scoped>
.sortable-ghost {
  opacity: 0.4;
}
</style>
