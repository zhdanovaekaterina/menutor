<script setup lang="ts">
import { ref } from 'vue'

const steps = defineModel<{ order: number; description: string }[]>({
  required: true,
})

const newStep = ref('')
const editingIdx = ref<number | null>(null)
const expanded = ref(true)

function add() {
  if (!newStep.value.trim()) return
  steps.value.push({ order: steps.value.length + 1, description: newStep.value.trim() })
  newStep.value = ''
}

function removeAt(index: number) {
  steps.value.splice(index, 1)
  steps.value.forEach((s, i) => { s.order = i + 1 })
}
</script>

<template>
  <div>
    <button
      type="button"
      class="flex items-center justify-between w-full bg-slate-100 px-3 py-2 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-200 transition-colors"
      @click="expanded = !expanded"
    >
      <span>Шаги приготовления</span>
      <svg
        :class="expanded ? 'rotate-180' : ''"
        class="w-4 h-4 transition-transform duration-200"
        xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"
      >
        <path stroke-linecap="round" stroke-linejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
      </svg>
    </button>
    <div v-show="expanded" class="pt-2 space-y-2">
      <div class="space-y-1">
        <div v-for="(s, i) in steps" :key="i"
             class="group flex items-center gap-1 px-2 py-1.5 rounded hover:bg-gray-50">
          <span class="text-xs text-gray-400 w-5 shrink-0 text-right">{{ i + 1 }}.</span>
          <template v-if="editingIdx === i">
            <input
              v-model="s.description"
              class="flex-1 border border-blue-300 rounded px-2 py-0.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-400"
              @keydown.enter="editingIdx = null"
              @blur="editingIdx = null"
              autofocus
            />
          </template>
          <template v-else>
            <span class="flex-1 text-sm">{{ s.description }}</span>
            <button
              type="button"
              class="opacity-40 hover:opacity-100 text-gray-400 hover:text-blue-500 shrink-0 transition-opacity text-xs px-1"
              title="Редактировать"
              @click="editingIdx = i"
            >&#x270E;</button>
            <button
              type="button"
              class="opacity-40 hover:opacity-100 text-gray-400 hover:text-red-500 shrink-0 transition-opacity text-xs px-1"
              title="Удалить шаг"
              @click="removeAt(i)"
            >&times;</button>
          </template>
        </div>
      </div>
      <div class="flex gap-2 mt-2">
        <input
          v-model="newStep"
          placeholder="Описание шага..."
          class="flex-1 border border-gray-300 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-400"
          @keydown.enter="add"
        />
        <button
          type="button"
          class="px-3 py-1.5 text-sm rounded border border-gray-300 hover:bg-gray-50 transition-colors"
          @click="add"
        >
          + Добавить
        </button>
      </div>
    </div>
  </div>
</template>
