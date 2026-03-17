<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import Sortable from 'sortablejs'
import type { MenuSlot } from '@/api/types'
import ItemRow from './ItemRow.vue'

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

function itemDetail(slot: MenuSlot) {
  if (slot.recipe_id != null) {
    const s = slot.servings_override ?? slot.quantity
    return s != null ? `${Number(s).toFixed(1)} п.` : ''
  }
  if (slot.product_id != null && slot.quantity != null) {
    return `${slot.quantity} ${slot.unit ?? ''}`
  }
  return ''
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
    @dragover="onDragOver"
    @dragleave="dragOver = false"
    @drop="onDrop"
  >
    <div ref="listRef" :data-day="day" :data-meal-type="mealType" class="flex flex-col gap-1 min-h-[8px] flex-1 max-h-40 overflow-y-auto">
      <ItemRow
        v-for="(slot, i) in cellSlots"
        :key="`${slot.recipe_id ?? ''}-${slot.product_id ?? ''}`"
        :name="itemName(slot)"
        :detail="itemDetail(slot)"
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
      <svg class="w-5 h-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
      </svg>
    </button>
  </div>
</template>

<style scoped>
.sortable-ghost {
  opacity: 0.4;
}
</style>
