<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import type { FamilyMember } from '@/api/types'
import MemberSelectorPopover from './MemberSelectorPopover.vue'

const props = defineProps<{
  open: boolean
  recipeName: string
  portions: string
  calculatedPieces: number
  pieces: string
  showDelete?: boolean
  familyMembers?: FamilyMember[]
  slotMemberIds?: number[]
}>()

const emit = defineEmits<{
  confirm: []
  cancel: []
  delete: []
  'update:pieces': [value: string]
  'member-ids-changed': [ids: number[]]
}>()

const inputRef = ref<HTMLInputElement | null>(null)
const showMemberSelector = ref(false)

const memberNames = computed(() => {
  if (!props.slotMemberIds?.length || !props.familyMembers?.length) return null
  return props.slotMemberIds
    .map(id => props.familyMembers!.find(m => m.id === id)?.name ?? `#${id}`)
    .join(', ')
})

const autoPortions = computed(() => {
  if (!props.slotMemberIds?.length || !props.familyMembers?.length) return null
  return props.familyMembers
    .filter(m => props.slotMemberIds!.includes(m.id))
    .reduce((sum, m) => sum + m.portion_multiplier, 0)
    .toFixed(1)
})

function onMemberSelectorApply(ids: number[]) {
  showMemberSelector.value = false
  emit('member-ids-changed', ids)
}

const piecesError = computed(() => {
  const val = parseInt(props.pieces)
  if (isNaN(val) || val < 1) return 'Минимум 1 шт'
  return ''
})

const isValid = computed(() => !piecesError.value)

watch(
  () => props.open,
  async (v) => {
    if (v) {
      await nextTick()
      inputRef.value?.focus()
      inputRef.value?.select()
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
  },
)

function onBlur() {
  // Округление до целого
  const val = parseFloat(props.pieces)
  if (!isNaN(val)) {
    const rounded = Math.max(1, Math.round(val))
    emit('update:pieces', String(rounded))
  }
}
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="fixed inset-0 bg-black/50 flex items-end sm:items-center justify-center z-50" @keydown.escape="emit('cancel')" @mousedown.self="emit('cancel')" @touchstart.self.passive="emit('cancel')">
      <div class="bg-white rounded-t-2xl sm:rounded-xl shadow-xl max-w-md w-full sm:mx-4 p-6">
        <!-- Drag indicator (mobile) -->
        <div class="w-10 h-1 bg-gray-300 rounded-full mx-auto mb-4 sm:hidden" />

        <h3 class="text-lg font-semibold mb-2">Количество: {{ recipeName }}</h3>

        <!-- Member info -->
        <div v-if="familyMembers?.length" class="mb-4">
          <p class="text-xs text-gray-500">
            <span v-if="memberNames">Участники: {{ memberNames }} (авто: {{ autoPortions }} порции)</span>
            <span v-else>Участники: все</span>
          </p>
          <button
            type="button"
            class="mt-1 text-xs text-blue-600 hover:text-blue-700 underline"
            @click="showMemberSelector = !showMemberSelector"
          >
            Изменить участников
          </button>
          <div v-if="showMemberSelector" class="mt-2">
            <MemberSelectorPopover
              :members="familyMembers"
              :selected-ids="slotMemberIds ?? []"
              @apply="onMemberSelectorApply"
              @cancel="showMemberSelector = false"
            />
          </div>
          <p class="text-xs text-amber-600 mt-1">Внимание: при изменении порций слот станет общим</p>
        </div>

        <!-- Порции (read-only) -->
        <label class="block text-sm font-medium text-gray-500 mb-1">Порции (авто)</label>
        <input
          :value="portions"
          type="text"
          readonly
          aria-readonly="true"
          aria-label="Порции (рассчитано автоматически)"
          class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm bg-gray-100 text-gray-600 cursor-not-allowed mb-4"
        />

        <!-- Количество (шт) -->
        <label class="block text-sm font-medium text-gray-700 mb-1">Количество (шт)</label>
        <input
          ref="inputRef"
          :value="pieces"
          type="number"
          min="1"
          step="1"
          aria-label="Количество штук"
          :class="[
            'w-full border rounded-lg px-3 py-2 text-sm outline-none',
            piecesError
              ? 'border-red-400 focus:ring-2 focus:ring-red-400'
              : 'border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
          ]"
          @input="emit('update:pieces', ($event.target as HTMLInputElement).value)"
          @blur="onBlur"
          @keydown.enter="isValid && emit('confirm')"
        />
        <p v-if="piecesError" class="text-xs text-red-500 mt-1" role="alert">{{ piecesError }}</p>
        <p class="text-xs text-gray-400 mt-1">Рассчитано: {{ calculatedPieces }} шт</p>

        <div class="flex justify-between items-center mt-6">
          <button
            v-if="showDelete"
            class="lg:hidden px-4 py-2 rounded-lg bg-red-50 text-red-600 text-sm hover:bg-red-100 transition-colors"
            @click="emit('delete')"
          >
            Удалить
          </button>
          <div class="flex gap-2 ml-auto">
            <button
              class="px-4 py-2 rounded-lg border border-gray-300 text-sm hover:bg-gray-50 transition-colors"
              @click="emit('cancel')"
            >
              Отмена
            </button>
            <button
              class="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              :disabled="!isValid"
              @click="emit('confirm')"
            >
              ОК
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>
