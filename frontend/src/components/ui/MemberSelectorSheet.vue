<script setup lang="ts">
import { computed, ref } from 'vue'
import type { FamilyMember } from '@/api/types'

const props = defineProps<{
  members: FamilyMember[]
  selectedIds: number[]
}>()

const emit = defineEmits<{
  apply: [ids: number[]]
  cancel: []
}>()

const localSelected = ref<number[]>([...props.selectedIds])

const portionSum = computed(() =>
  props.members
    .filter(m => localSelected.value.includes(m.id))
    .reduce((sum, m) => sum + m.portion_multiplier, 0)
    .toFixed(1)
)

function toggleMember(id: number) {
  const idx = localSelected.value.indexOf(id)
  if (idx !== -1) {
    localSelected.value = localSelected.value.filter(x => x !== id)
  } else {
    localSelected.value = [...localSelected.value, id]
  }
}

// Sheet drag-to-dismiss
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
    emit('cancel')
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
        @click="emit('cancel')"
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
        aria-label="Выбор участников"
        @touchstart="onTouchStart"
        @touchmove="onTouchMove"
        @touchend="onTouchEnd"
      >
        <!-- Handle -->
        <div data-sheet-handle class="flex justify-center py-3 cursor-grab shrink-0">
          <div class="w-9 h-1 rounded-full bg-gray-300" />
        </div>

        <!-- Header -->
        <div class="px-4 pb-2 shrink-0">
          <h3 class="font-semibold text-base">Выберите участников</h3>
        </div>

        <!-- Member list -->
        <div class="flex-1 overflow-y-auto px-4 pb-2">
          <div class="flex flex-col gap-3 py-2">
            <label
              v-for="member in members"
              :key="member.id"
              class="flex items-center gap-3 cursor-pointer py-1"
            >
              <input
                type="checkbox"
                :checked="localSelected.includes(member.id)"
                class="w-5 h-5 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                @change="toggleMember(member.id)"
              />
              <span class="text-base text-gray-700">{{ member.name }} (×{{ member.portion_multiplier }})</span>
            </label>
          </div>
          <p class="text-sm text-gray-500 mt-2">Порции: {{ portionSum }}</p>
        </div>

        <!-- Actions -->
        <div class="flex gap-3 px-4 pb-4 pt-2 shrink-0 border-t border-gray-100">
          <button
            class="flex-1 py-3 rounded-xl border border-gray-300 text-sm font-medium hover:bg-gray-50 transition-colors"
            @click="emit('cancel')"
          >
            Отмена
          </button>
          <button
            class="flex-1 py-3 rounded-xl bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 transition-colors"
            @click="emit('apply', localSelected)"
          >
            Применить
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
