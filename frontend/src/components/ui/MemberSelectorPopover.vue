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
</script>

<template>
  <div class="border border-gray-200 rounded-xl bg-white shadow-lg p-4 w-full">
    <p class="text-sm font-medium text-gray-700 mb-3">Выберите участников:</p>
    <div class="flex flex-col gap-2 mb-3">
      <label
        v-for="member in members"
        :key="member.id"
        class="flex items-center gap-2 cursor-pointer"
      >
        <input
          type="checkbox"
          :checked="localSelected.includes(member.id)"
          class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          @change="toggleMember(member.id)"
        />
        <span class="text-sm text-gray-700">{{ member.name }} (×{{ member.portion_multiplier }})</span>
      </label>
    </div>
    <p class="text-xs text-gray-500 mb-4">Порции: {{ portionSum }}</p>
    <div class="flex gap-2">
      <button
        class="flex-1 px-3 py-2 rounded-lg border border-gray-300 text-sm hover:bg-gray-50 transition-colors"
        @click="emit('cancel')"
      >
        Отмена
      </button>
      <button
        class="flex-1 px-3 py-2 rounded-lg bg-blue-600 text-white text-sm hover:bg-blue-700 transition-colors"
        @click="emit('apply', localSelected)"
      >
        Применить
      </button>
    </div>
  </div>
</template>
