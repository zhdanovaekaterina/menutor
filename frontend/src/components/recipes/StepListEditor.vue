<script setup lang="ts">
import { ref } from 'vue'

const steps = defineModel<{ order: number; description: string }[]>({
  required: true,
})

const newStep = ref('')
const editingIdx = ref<number | null>(null)

function add() {
  if (!newStep.value.trim()) return
  steps.value.push({ order: steps.value.length + 1, description: newStep.value.trim() })
  newStep.value = ''
}

function removeLast() {
  steps.value.pop()
}
</script>

<template>
  <details open>
    <summary class="bg-slate-200 px-3 py-2 rounded font-medium text-sm cursor-pointer select-none hover:bg-slate-300">
      Шаги приготовления
    </summary>
    <div class="pt-2 space-y-2">
      <ol class="list-decimal list-inside text-sm space-y-1">
        <li v-for="(s, i) in steps" :key="s.order" class="group flex items-center gap-1 px-2 py-1 rounded hover:bg-gray-100">
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
            <span class="flex-1">{{ s.description }}</span>
            <button
              class="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-blue-500 shrink-0"
              title="Редактировать"
              @click="editingIdx = i"
            >&#x270E;</button>
          </template>
        </li>
      </ol>
      <div class="flex gap-2">
        <input v-model="newStep" placeholder="Описание шага..."
          class="flex-1 border border-gray-300 rounded px-2 py-1.5 text-sm"
          @keydown.enter="add" />
        <button class="px-3 py-1 text-xs rounded border border-gray-300 hover:bg-gray-50" @click="add">+</button>
        <button class="px-3 py-1 text-xs rounded border border-gray-300 text-red-600 hover:bg-red-50" @click="removeLast">&minus;</button>
      </div>
    </div>
  </details>
</template>
