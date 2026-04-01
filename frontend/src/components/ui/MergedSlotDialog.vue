<script setup lang="ts">
import { watch } from 'vue'
import type { FamilyMember, MenuSlot } from '@/api/types'

const props = defineProps<{
  recipeName: string
  totalServings: number
  slots: MenuSlot[]
  familyMembers: FamilyMember[]
}>()

const emit = defineEmits<{
  close: []
  'edit-slot': [slot: MenuSlot]
  'remove-slot': [slot: MenuSlot]
}>()

watch(
  () => props.slots.length,
  (v) => {
    if (v > 0) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
  },
  { immediate: true }
)

function formatNumber(n: number): string {
  return n % 1 === 0 ? String(n) : n.toFixed(1)
}

function memberNames(slot: MenuSlot): string {
  if (!slot.member_ids?.length) return 'Все'
  return slot.member_ids
    .map(id => props.familyMembers.find(m => m.id === id)?.name ?? `#${id}`)
    .join(', ')
}
</script>

<template>
  <Teleport to="body">
    <div
      class="fixed inset-0 bg-black/50 flex items-end sm:items-center justify-center z-50"
      @keydown.escape="emit('close')"
      @mousedown.self="emit('close')"
      @touchstart.self.passive="emit('close')"
    >
      <div class="bg-white rounded-t-2xl sm:rounded-xl shadow-xl max-w-md w-full sm:mx-4 p-6">
        <!-- Drag indicator (mobile) -->
        <div class="w-10 h-1 bg-gray-300 rounded-full mx-auto mb-4 sm:hidden" />

        <h3 class="text-lg font-semibold mb-1">{{ recipeName }}</h3>
        <p class="text-sm text-gray-500 mb-4">
          Суммарно: {{ formatNumber(totalServings) }} порции
        </p>

        <div class="flex flex-col gap-2 mb-6">
          <div
            v-for="(slot, i) in slots"
            :key="i"
            class="flex items-center gap-2 px-3 py-2 rounded-lg bg-gray-50 border border-gray-200"
          >
            <span class="flex-1 text-sm text-gray-700 truncate">{{ memberNames(slot) }}</span>
            <span class="text-sm text-gray-500 whitespace-nowrap shrink-0">
              {{ formatNumber(slot.servings_override ?? 0) }} п.
            </span>
            <button
              class="text-xs px-2 py-1 rounded border border-gray-300 text-gray-600 hover:bg-gray-100 transition-colors shrink-0"
              @click="emit('edit-slot', slot)"
            >
              Ред.
            </button>
            <button
              class="text-xs px-2 py-1 rounded border border-red-200 text-red-500 hover:bg-red-50 transition-colors shrink-0"
              @click="emit('remove-slot', slot)"
            >
              &times;
            </button>
          </div>
        </div>

        <div class="flex justify-end">
          <button
            class="px-4 py-2 rounded-lg border border-gray-300 text-sm hover:bg-gray-50 transition-colors"
            @click="emit('close')"
          >
            Закрыть
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
