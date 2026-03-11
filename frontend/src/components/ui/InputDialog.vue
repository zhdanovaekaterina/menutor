<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  open: boolean
  title: string
  label: string
  initialValue?: string
  inputType?: string
}>()

const emit = defineEmits<{ confirm: [value: string]; cancel: [] }>()

const value = ref(props.initialValue ?? '')

watch(
  () => props.open,
  (v) => {
    if (v) value.value = props.initialValue ?? ''
  },
)
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white rounded-xl shadow-xl max-w-md w-full mx-4 p-6">
        <h3 class="text-lg font-semibold mb-4">{{ title }}</h3>
        <label class="block text-sm font-medium text-gray-700 mb-1">{{ label }}</label>
        <input
          v-model="value"
          :type="inputType ?? 'text'"
          class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
          @keydown.enter="emit('confirm', value)"
        />
        <div class="flex justify-end gap-2 mt-6">
          <button
            class="px-4 py-2 rounded-lg border border-gray-300 text-sm hover:bg-gray-50"
            @click="emit('cancel')"
          >
            Отмена
          </button>
          <button
            class="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm hover:bg-blue-700"
            @click="emit('confirm', value)"
          >
            ОК
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
