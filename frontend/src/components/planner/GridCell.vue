<script setup lang="ts">
import { computed, ref } from 'vue'
import type { MenuSlot } from '@/api/types'
import ItemRow from './ItemRow.vue'

const props = defineProps<{
  day: number
  mealType: string
  slots: MenuSlot[]
  recipeNames: Record<number, string>
  productNames: Record<number, string>
}>()

const emit = defineEmits<{
  addItem: [data: { type: 'recipe' | 'product'; id: number }]
  removeItem: [data: { recipe_id?: number | null; product_id?: number | null }]
  editItem: [slot: MenuSlot]
}>()

const dragOver = ref(false)

const cellSlots = computed(() =>
  props.slots.filter((s) => s.day === props.day && s.meal_type === props.mealType),
)

function itemName(slot: MenuSlot) {
  if (slot.recipe_id != null) return props.recipeNames[slot.recipe_id] ?? `#${slot.recipe_id}`
  if (slot.product_id != null) return props.productNames[slot.product_id] ?? `#${slot.product_id}`
  return '?'
}

function itemDetail(slot: MenuSlot) {
  if (slot.recipe_id != null) {
    const s = slot.servings_override ?? slot.quantity
    return s != null ? `${s} п.` : ''
  }
  if (slot.product_id != null && slot.quantity != null) {
    return `${slot.quantity} ${slot.unit ?? ''}`
  }
  return ''
}

function onDrop(e: DragEvent) {
  dragOver.value = false
  const raw = e.dataTransfer?.getData('application/json')
  if (!raw) return
  try {
    const data = JSON.parse(raw) as { type: 'recipe' | 'product'; id: number }
    emit('addItem', data)
  } catch { /* ignore */ }
}
</script>

<template>
  <div
    :class="dragOver ? 'ring-2 ring-blue-300 bg-blue-50/50' : 'bg-white'"
    class="min-h-[80px] p-1 flex flex-col gap-1"
    @dragover.prevent="dragOver = true"
    @dragleave="dragOver = false"
    @drop.prevent="onDrop"
  >
    <ItemRow
      v-for="(slot, i) in cellSlots"
      :key="i"
      :name="itemName(slot)"
      :detail="itemDetail(slot)"
      :variant="slot.recipe_id != null ? 'recipe' : 'product'"
      @remove="emit('removeItem', { recipe_id: slot.recipe_id, product_id: slot.product_id })"
      @click="emit('editItem', slot)"
    />
  </div>
</template>
