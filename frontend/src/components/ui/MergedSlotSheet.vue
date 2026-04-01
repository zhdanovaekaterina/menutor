<script setup lang="ts">
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

function formatNumber(n: number): string {
  return n % 1 === 0 ? String(n) : n.toFixed(1)
}

function memberNames(slot: MenuSlot): string {
  if (!slot.member_ids?.length) return 'Все'
  return slot.member_ids
    .map(id => props.familyMembers.find(m => m.id === id)?.name ?? `#${id}`)
    .join(', ')
}

// Sheet drag-to-dismiss
import { ref } from 'vue'
const dragY = ref(0)
const dragging = ref(false)
let startY = 0

function onTouchStart(e: TouchEvent) {
  const target = e.target as HTMLElement
  if (!target.closest('[data-sheet-handle]')) return
  if (!e.touches[0]) return
  startY = e.touches[0].clientY
  dragging.value = true
  dragY.value = 0
}

function onTouchMove(e: TouchEvent) {
  if (!dragging.value) return
  if (!e.touches[0]) return
  const delta = e.touches[0].clientY - startY
  if (delta > 0) {
    dragY.value = delta
    e.preventDefault()
  }
}

function onTouchEnd() {
  if (!dragging.value) return
  dragging.value = false
  if (dragY.value > 80) {
    emit('close')
  }
  dragY.value = 0
}
</script>

<template>
  <Teleport to="body">
    <!-- Backdrop -->
    <Transition name="fade">
      <div
        class="lg:hidden fixed inset-0 bg-black/30 z-40"
        @click="emit('close')"
      />
    </Transition>

    <!-- Bottom Sheet -->
    <Transition name="sheet">
      <div
        class="lg:hidden fixed inset-x-0 bottom-0 z-50 bg-white rounded-t-2xl shadow-2xl flex flex-col"
        style="max-height: 70vh;"
        :style="dragging ? { transform: `translateY(${dragY}px)` } : {}"
        role="dialog"
        aria-modal="true"
        :aria-label="`Блюдо: ${recipeName}`"
        @touchstart="onTouchStart"
        @touchmove="onTouchMove"
        @touchend="onTouchEnd"
      >
        <!-- Handle -->
        <div data-sheet-handle class="flex justify-center py-3 cursor-grab shrink-0">
          <div class="w-9 h-1 rounded-full bg-gray-300" />
        </div>

        <!-- Header -->
        <div class="px-4 pb-1 shrink-0">
          <h3 class="font-semibold text-base">{{ recipeName }}</h3>
          <p class="text-sm text-gray-500">Суммарно: {{ formatNumber(totalServings) }} порции</p>
        </div>

        <!-- Sub-slot list -->
        <div class="flex-1 overflow-y-auto px-4 py-3">
          <div class="flex flex-col gap-2">
            <div
              v-for="(slot, i) in slots"
              :key="i"
              class="flex items-center gap-2 px-3 py-3 rounded-xl bg-gray-50 border border-gray-200"
            >
              <span class="flex-1 text-sm text-gray-700 truncate">{{ memberNames(slot) }}</span>
              <span class="text-sm text-gray-500 whitespace-nowrap shrink-0">
                {{ formatNumber(slot.servings_override ?? 0) }} п.
              </span>
              <button
                class="text-sm px-3 py-1.5 rounded-lg border border-gray-300 text-gray-600 active:bg-gray-100 transition-colors shrink-0"
                @click="emit('edit-slot', slot)"
              >
                Ред.
              </button>
              <button
                class="text-sm px-3 py-1.5 rounded-lg border border-red-200 text-red-500 active:bg-red-50 transition-colors shrink-0"
                @click="emit('remove-slot', slot)"
              >
                &times;
              </button>
            </div>
          </div>
        </div>

        <!-- Close button -->
        <div class="px-4 pb-4 pt-2 shrink-0 border-t border-gray-100">
          <button
            class="w-full py-3 rounded-xl border border-gray-300 text-sm font-medium hover:bg-gray-50 transition-colors"
            @click="emit('close')"
          >
            Закрыть
          </button>
        </div>

        <!-- Safe area spacer -->
        <div class="shrink-0" style="height: env(safe-area-inset-bottom, 0px)" />
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.sheet-enter-active { transition: transform 0.3s cubic-bezier(0.32, 0.72, 0, 1); }
.sheet-leave-active { transition: transform 0.2s ease-out; }
.sheet-enter-from, .sheet-leave-to { transform: translateY(100%); }

@media (prefers-reduced-motion: reduce) {
  .fade-enter-active, .fade-leave-active,
  .sheet-enter-active, .sheet-leave-active {
    transition-duration: 0.01ms;
  }
}
</style>
